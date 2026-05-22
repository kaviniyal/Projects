"""
ETL — Extract Stage
====================
Reads raw knowledge-article datasets from CSV or JSON files into Pandas
DataFrames.  Supports multiple input sources and basic schema validation.

Usage (standalone):
    python -m etl.extract
"""

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Expected columns (raw dataset schema)
# ---------------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "id", "title", "category", "tags", "views",
    "author_name", "author_email", "summary", "content", "status",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file and return a raw DataFrame.

    Parameters
    ----------
    file_path : str or Path
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Raw, unprocessed DataFrame with all columns as strings.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If required columns are missing from the CSV.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    logger.info("Extracting CSV: %s", path)
    df = pd.read_csv(path, dtype=str, encoding="utf-8")
    df.columns = df.columns.str.strip().str.lower()

    _validate_schema(df, path)
    logger.info("  → %d rows extracted from %s", len(df), path.name)
    return df


def extract_json(file_path: str | Path) -> pd.DataFrame:
    """
    Read a JSON file (array of objects or records-oriented) and return a
    raw DataFrame.

    Parameters
    ----------
    file_path : str or Path
        Path to the JSON file.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    logger.info("Extracting JSON: %s", path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict) and "articles" in data:
        data = data["articles"]

    df = pd.DataFrame(data).astype(str)
    df.columns = df.columns.str.strip().str.lower()

    _validate_schema(df, path)
    logger.info("  → %d rows extracted from %s", len(df), path.name)
    return df


def extract_all(datasets_dir: str | Path) -> pd.DataFrame:
    """
    Scan *datasets_dir* for all .csv and .json files, extract each one, and
    concatenate into a single DataFrame.

    Parameters
    ----------
    datasets_dir : str or Path
        Directory that holds dataset files.

    Returns
    -------
    pd.DataFrame
        Combined DataFrame with a ``source_file`` column added.
    """
    datasets_dir = Path(datasets_dir)
    frames = []

    for csv_file in sorted(datasets_dir.glob("*.csv")):
        df = extract_csv(csv_file)
        df["source_file"] = csv_file.name
        frames.append(df)

    for json_file in sorted(datasets_dir.glob("*.json")):
        df = extract_json(json_file)
        df["source_file"] = json_file.name
        frames.append(df)

    if not frames:
        raise ValueError(f"No CSV or JSON dataset files found in: {datasets_dir}")

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Extracted total %d rows from %d file(s).", len(combined), len(frames))
    return combined


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_schema(df: pd.DataFrame, source: Path) -> None:
    """Raise ValueError if required columns are absent from *df*."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset '{source.name}' is missing required columns: {sorted(missing)}"
        )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    datasets_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "datasets"

    try:
        raw = extract_all(datasets_path)
        print(f"\n✓ Extracted {len(raw)} rows total.")
        print(raw.head(3).to_string())
    except Exception as exc:
        logger.error("Extraction failed: %s", exc)
        sys.exit(1)
