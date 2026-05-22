"""
ETL Pipeline – Helpdesk Ticket Analytics
=========================================
Phase 2 Capstone: Extract → Transform → Load

Stages:
  1. EXTRACT  – Read raw CSV from datasets/
  2. TRANSFORM – Deduplicate, normalize categories/priorities/statuses,
                 compute resolution time, enrich month/date columns
  3. LOAD      – Write cleaned data to analytics.db (SQLite)
                 and log each run in etl_runs table

Usage:
  python etl/etl_pipeline.py
  python etl/etl_pipeline.py --source datasets/tickets_historical.csv
  python etl/etl_pipeline.py --sync-live   (also syncs from live helpdesk.db)
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime

import pandas as pd

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV = os.path.join(BASE_DIR, "datasets", "tickets_historical.csv")
ANALYTICS_DB = os.path.join(BASE_DIR, "backend", "analytics.db")
LIVE_DB = os.path.join(BASE_DIR, "backend", "helpdesk.db")

# Canonical category mapping (handles typos/variants)
CATEGORY_MAP = {
    "vpn": "VPN Issue",
    "vpn issue": "VPN Issue",
    "vpn problem": "VPN Issue",
    "pwd reset": "Password Reset",
    "password reset": "Password Reset",
    "password_reset": "Password Reset",
    "software install": "Software Installation",
    "sw installation": "Software Installation",
    "software installation": "Software Installation",
    "laptop problem": "Laptop Issue",
    "laptop issue": "Laptop Issue",
    "email problem": "Email Access",
    "email access": "Email Access",
    "network issue": "Network Connectivity",
    "network connectivity": "Network Connectivity",
    "network problem": "Network Connectivity",
    "hw request": "Hardware Request",
    "hardware req": "Hardware Request",
    "hardware request": "Hardware Request",
}

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES = {"Open", "In Progress", "Resolved", "Closed"}


# ──────────────────────────────────────────────────────────────────────────────
# Database Setup
# ──────────────────────────────────────────────────────────────────────────────
def setup_analytics_db(conn: sqlite3.Connection) -> None:
    """Create analytics tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS reporting_tickets (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ticket_id    TEXT UNIQUE,
            employee_name       TEXT,
            department          TEXT,
            issue_category      TEXT,
            description         TEXT,
            priority            TEXT,
            status              TEXT,
            resolution_notes    TEXT,
            created_at          DATETIME,
            resolved_at         DATETIME,
            resolution_time_days REAL,
            created_date        DATE,
            created_month       TEXT,
            source              TEXT DEFAULT 'csv_import',
            loaded_at           DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_rt_category  ON reporting_tickets(issue_category);
        CREATE INDEX IF NOT EXISTS idx_rt_dept       ON reporting_tickets(department);
        CREATE INDEX IF NOT EXISTS idx_rt_priority   ON reporting_tickets(priority);
        CREATE INDEX IF NOT EXISTS idx_rt_status     ON reporting_tickets(status);
        CREATE INDEX IF NOT EXISTS idx_rt_month      ON reporting_tickets(created_month);

        CREATE TABLE IF NOT EXISTS etl_runs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_file         TEXT,
            records_extracted   INTEGER,
            records_after_dedup INTEGER,
            records_transformed INTEGER,
            records_loaded      INTEGER,
            duplicates_removed  INTEGER,
            status              TEXT,
            error_message       TEXT
        );
    """)
    conn.commit()


# ──────────────────────────────────────────────────────────────────────────────
# STAGE 1 – EXTRACT
# ──────────────────────────────────────────────────────────────────────────────
def extract(csv_path: str) -> pd.DataFrame:
    """Read raw CSV into a DataFrame."""
    print(f"\n{'='*60}")
    print("STAGE 1 – EXTRACT")
    print(f"{'='*60}")
    print(f"  Source : {csv_path}")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    print(f"  Rows   : {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    return df


def extract_live_db(live_db_path: str) -> pd.DataFrame:
    """Extract live tickets from helpdesk.db."""
    if not os.path.exists(live_db_path):
        print(f"  [SKIP] Live DB not found at {live_db_path}")
        return pd.DataFrame()

    conn = sqlite3.connect(live_db_path)
    df = pd.read_sql_query(
        """SELECT ticket_id, employee_name, department, issue_category,
                  description, priority, status, resolution_notes,
                  created_at, updated_at AS resolved_at
           FROM tickets""",
        conn,
        dtype=str,
    )
    conn.close()
    df["source"] = "live_db"
    print(f"  Live DB: {len(df)} tickets from helpdesk.db")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# STAGE 2 – TRANSFORM
# ──────────────────────────────────────────────────────────────────────────────
def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Clean, normalize, and enrich the extracted data."""
    print(f"\n{'='*60}")
    print("STAGE 2 – TRANSFORM")
    print(f"{'='*60}")
    raw_count = len(df)

    # ── 2.1  Ensure source column ────────────────────────────────────────────
    if "source" not in df.columns:
        df["source"] = "csv_import"

    # ── 2.2  Rename ticket_id → source_ticket_id ────────────────────────────
    if "ticket_id" in df.columns:
        df.rename(columns={"ticket_id": "source_ticket_id"}, inplace=True)

    # ── 2.3  Drop fully blank rows ───────────────────────────────────────────
    df.replace("", pd.NA, inplace=True)
    df.dropna(subset=["employee_name", "description"], inplace=True)
    print(f"  After blank-row drop : {len(df)} rows")

    # ── 2.4  Remove exact duplicates (same employee + category + description + date) ──
    dedup_cols = ["employee_name", "issue_category", "description", "created_at"]
    df_dedup = df.drop_duplicates(subset=dedup_cols, keep="first").copy()
    dupes_removed = raw_count - len(df_dedup)
    print(f"  Duplicates removed   : {dupes_removed}")
    print(f"  After dedup          : {len(df_dedup)} rows")
    df = df_dedup

    # ── 2.5  Normalize issue_category ───────────────────────────────────────
    def normalize_category(val):
        if pd.isna(val):
            return "Unknown"
        key = str(val).strip().lower()
        return CATEGORY_MAP.get(key, str(val).strip().title())

    original_cats = df["issue_category"].copy()
    df["issue_category"] = df["issue_category"].apply(normalize_category)
    cat_fixed = (original_cats.fillna("") != df["issue_category"].fillna("")).sum()
    print(f"  Categories normalized: {cat_fixed} values corrected")

    # ── 2.6  Normalize priority (title-case, validate) ───────────────────────
    df["priority"] = df["priority"].str.strip().str.title()
    df.loc[~df["priority"].isin(VALID_PRIORITIES), "priority"] = "Medium"

    # ── 2.7  Normalize status ────────────────────────────────────────────────
    df["status"] = df["status"].str.strip().str.title()
    df.loc[~df["status"].isin(VALID_STATUSES), "status"] = "Open"

    # ── 2.8  Parse dates ─────────────────────────────────────────────────────
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce")

    # ── 2.9  Compute resolution_time_days ────────────────────────────────────
    df["resolution_time_days"] = (
        (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 86400
    ).round(2)
    df.loc[df["resolution_time_days"] < 0, "resolution_time_days"] = pd.NA

    # ── 2.10  Enrich date columns ────────────────────────────────────────────
    df["created_date"] = df["created_at"].dt.date
    df["created_month"] = df["created_at"].dt.to_period("M").astype(str)

    # ── 2.11  Fill nulls ─────────────────────────────────────────────────────
    df["resolution_notes"] = df["resolution_notes"].fillna("")
    df["department"] = df["department"].fillna("Unknown")

    # ── 2.12  String cleanup ─────────────────────────────────────────────────
    df["employee_name"] = df["employee_name"].str.strip().str.title()
    df["department"] = df["department"].str.strip().str.title()

    print(f"  Final transformed    : {len(df)} rows")
    print("\n  Category distribution after normalization:")
    for cat, cnt in df["issue_category"].value_counts().items():
        print(f"    {cat:<30} {cnt:>4}")

    return df, dupes_removed


# ──────────────────────────────────────────────────────────────────────────────
# STAGE 3 – LOAD
# ──────────────────────────────────────────────────────────────────────────────
def load(df: pd.DataFrame, conn: sqlite3.Connection) -> int:
    """Upsert transformed records into reporting_tickets."""
    print(f"\n{'='*60}")
    print("STAGE 3 – LOAD")
    print(f"{'='*60}")

    load_cols = [
        "source_ticket_id", "employee_name", "department", "issue_category",
        "description", "priority", "status", "resolution_notes",
        "created_at", "resolved_at", "resolution_time_days",
        "created_date", "created_month", "source"
    ]

    # Keep only columns that exist in df
    cols_to_load = [c for c in load_cols if c in df.columns]
    df_load = df[cols_to_load].copy()

    # Convert dates to strings for SQLite
    for col in ["created_at", "resolved_at"]:
        if col in df_load.columns:
            df_load[col] = df_load[col].astype(str).replace("NaT", "")

    df_load["created_date"] = df_load["created_date"].astype(str).replace("NaT", "")

    loaded = 0
    skipped = 0
    for _, row in df_load.iterrows():
        try:
            conn.execute(
                f"""INSERT OR IGNORE INTO reporting_tickets
                    ({', '.join(cols_to_load)})
                    VALUES ({', '.join(['?'] * len(cols_to_load))})""",
                [row.get(c, "") for c in cols_to_load],
            )
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                loaded += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [WARN] Row skipped: {e}")

    conn.commit()
    print(f"  Records inserted : {loaded}")
    print(f"  Already existed  : {skipped} (skipped)")
    return loaded


# ──────────────────────────────────────────────────────────────────────────────
# ETL Run Logger
# ──────────────────────────────────────────────────────────────────────────────
def log_run(conn, source_file, extracted, after_dedup, transformed, loaded, dupes, status, error=""):
    conn.execute(
        """INSERT INTO etl_runs
           (source_file, records_extracted, records_after_dedup,
            records_transformed, records_loaded, duplicates_removed, status, error_message)
           VALUES (?,?,?,?,?,?,?,?)""",
        (source_file, extracted, after_dedup, transformed, loaded, dupes, status, error),
    )
    conn.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def run_etl(csv_path: str = DEFAULT_CSV, sync_live: bool = False):
    print("\n" + "=" * 60)
    print("  HELPDESK ETL PIPELINE – Phase 2")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    os.makedirs(os.path.dirname(ANALYTICS_DB), exist_ok=True)
    conn = sqlite3.connect(ANALYTICS_DB)
    setup_analytics_db(conn)

    extracted = 0
    after_dedup = 0
    loaded_total = 0
    dupes_total = 0

    try:
        # ── CSV source ───────────────────────────────────────────────────────
        df_csv = extract(csv_path)
        extracted += len(df_csv)

        if sync_live:
            df_live = extract_live_db(LIVE_DB)
            if not df_live.empty:
                df_live.rename(columns={"ticket_id": "source_ticket_id"}, inplace=True)
                df_csv = pd.concat([df_csv, df_live], ignore_index=True)
                print(f"  Combined total       : {len(df_csv)} rows")

        df_transformed, dupes = transform(df_csv)
        dupes_total += dupes
        after_dedup = len(df_csv) - dupes
        loaded = load(df_transformed, conn)
        loaded_total += loaded

        log_run(
            conn, csv_path, extracted, after_dedup,
            len(df_transformed), loaded_total, dupes_total, "SUCCESS"
        )

        print(f"\n{'='*60}")
        print("  ETL COMPLETE [SUCCESS]")
        print(f"  Extracted : {extracted}")
        print(f"  Duplicates: {dupes_total}")
        print(f"  Loaded    : {loaded_total}")
        print(f"  DB Path   : {ANALYTICS_DB}")
        print(f"{'='*60}\n")

    except Exception as exc:
        log_run(conn, csv_path, extracted, after_dedup, 0, 0, dupes_total, "FAILED", str(exc))
        print(f"\n[ERROR] ETL failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Helpdesk ETL Pipeline")
    parser.add_argument("--source", default=DEFAULT_CSV, help="Path to input CSV")
    parser.add_argument("--sync-live", action="store_true", help="Also sync from live helpdesk.db")
    args = parser.parse_args()
    run_etl(csv_path=args.source, sync_live=args.sync_live)
