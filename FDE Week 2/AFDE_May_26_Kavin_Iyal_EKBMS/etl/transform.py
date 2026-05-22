"""
ETL — Transform Stage
======================
Cleans, normalises, and enriches the raw extracted DataFrame.

Transformation steps
--------------------
1.  Strip whitespace from all string columns.
2.  Deduplicate rows (by ``id`` and ``title``).
3.  Drop rows where title or content is blank.
4.  Normalise ``category`` values to the set used by the KB system.
5.  Parse ``tags`` (comma-separated string) → list of clean tag strings.
6.  Cast ``views`` to integer (default 0 on errors).
7.  Parse ``created_date`` and ``published_date`` to datetime.
8.  Normalise ``status`` to one of the valid KB statuses.
9.  Add derived columns: ``tag_count``, ``content_word_count``.
10. Add ``etl_loaded_at`` timestamp.

Usage (standalone):
    python -m etl.transform
"""

import logging
from datetime import datetime, timezone
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CATEGORIES = {
    "HR Policies",
    "IT Support",
    "Infrastructure",
    "Training Materials",
    "Finance",
    "Operations",
}

# Fuzzy mapping: normalise common misspellings / aliases → canonical name
CATEGORY_MAP = {
    "hr": "HR Policies",
    "hr policy": "HR Policies",
    "hr policies": "HR Policies",
    "human resources": "HR Policies",
    "it": "IT Support",
    "it support": "IT Support",
    "tech support": "IT Support",
    "helpdesk": "IT Support",
    "infra": "Infrastructure",
    "infrastructure": "Infrastructure",
    "network": "Infrastructure",
    "training": "Training Materials",
    "training materials": "Training Materials",
    "learning": "Training Materials",
    "finance": "Finance",
    "accounting": "Finance",
    "operations": "Operations",
    "ops": "Operations",
}

VALID_STATUSES = {"Draft", "Pending Approval", "Approved", "Rejected", "Archived"}

STATUS_MAP = {
    "draft": "Draft",
    "pending": "Pending Approval",
    "pending approval": "Pending Approval",
    "approved": "Approved",
    "published": "Approved",
    "rejected": "Rejected",
    "archived": "Archived",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all transformation steps to a raw extracted DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame from the extract stage.

    Returns
    -------
    pd.DataFrame
        Cleaned and enriched DataFrame ready for the load stage.
    """
    logger.info("Transforming %d rows …", len(df))
    df = df.copy()

    df = _strip_whitespace(df)
    df = _deduplicate(df)
    df = _drop_empty_required(df)
    df = _normalise_category(df)
    df = _parse_tags(df)
    df = _cast_views(df)
    df = _parse_dates(df)
    df = _normalise_status(df)
    df = _add_derived_columns(df)

    logger.info("  → %d rows after transformation.", len(df))
    return df


# ---------------------------------------------------------------------------
# Individual transformation helpers
# ---------------------------------------------------------------------------

def _strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all string columns."""
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())
    return df


def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows by (id) first, then by (title)."""
    before = len(df)
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"], keep="first")
    df = df.drop_duplicates(subset=["title"], keep="first")
    removed = before - len(df)
    if removed:
        logger.info("  Deduplication removed %d duplicate rows.", removed)
    return df


def _drop_empty_required(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where title or content is empty/null."""
    before = len(df)
    df = df[df["title"].notna() & df["title"].str.strip().ne("")]
    df = df[df["content"].notna() & df["content"].str.strip().ne("")]
    removed = before - len(df)
    if removed:
        logger.info("  Dropped %d rows with missing title/content.", removed)
    return df


def _normalise_category(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw category strings to canonical category names."""
    def _map(raw: str) -> str:
        clean = str(raw).strip()
        canonical = CATEGORY_MAP.get(clean.lower())
        if canonical:
            return canonical
        # Check if already a valid category (case-insensitive)
        for valid in VALID_CATEGORIES:
            if valid.lower() == clean.lower():
                return valid
        logger.warning("  Unknown category '%s' — defaulting to 'Operations'.", clean)
        return "Operations"

    df["category"] = df["category"].apply(_map)
    return df


def _parse_tags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the comma-separated tags string into a cleaned list stored as
    the ``tags_list`` column; keep the normalised string in ``tags``.
    """
    def _clean_tags(raw: str) -> List[str]:
        if pd.isna(raw) or str(raw).strip() in ("", "nan"):
            return []
        parts = str(raw).split(",")
        return [t.strip().lower().replace(" ", "-") for t in parts if t.strip()]

    df["tags_list"] = df["tags"].apply(_clean_tags)
    # Rebuild canonical tags string
    df["tags"] = df["tags_list"].apply(lambda lst: ",".join(lst))
    return df


def _cast_views(df: pd.DataFrame) -> pd.DataFrame:
    """Cast view_count to integer; replace nulls/errors with 0."""
    df["views"] = pd.to_numeric(df["views"], errors="coerce").fillna(0).astype(int)
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse created_date and published_date to datetime objects (UTC-naive)."""
    for col in ("created_date", "published_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _normalise_status(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw status strings to canonical KB statuses."""
    def _map(raw: str) -> str:
        clean = str(raw).strip()
        mapped = STATUS_MAP.get(clean.lower())
        if mapped:
            return mapped
        for valid in VALID_STATUSES:
            if valid.lower() == clean.lower():
                return valid
        logger.warning("  Unknown status '%s' — defaulting to 'Draft'.", clean)
        return "Draft"

    df["status"] = df["status"].apply(_map)
    return df


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add tag_count, content_word_count, and etl_loaded_at."""
    df["tag_count"] = df["tags_list"].apply(len)
    df["content_word_count"] = df["content"].str.split().str.len().fillna(0).astype(int)
    df["etl_loaded_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    return df


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path
    from etl.extract import extract_all

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    datasets_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "datasets"

    try:
        raw = extract_all(datasets_path)
        clean = transform(raw)
        print(f"\n✓ Transformation complete — {len(clean)} rows.")
        print(clean[["title", "category", "tags", "views", "status", "tag_count", "content_word_count"]].head(10).to_string())
    except Exception as exc:
        logger.error("Transformation failed: %s", exc)
        sys.exit(1)
