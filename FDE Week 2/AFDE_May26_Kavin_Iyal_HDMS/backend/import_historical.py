"""
import_historical.py
====================
One-shot script that loads tickets_historical.csv into the live helpdesk.db
so they appear on the "All Tickets" page alongside manually-created tickets.

Runs the same normalisation as the ETL pipeline (category aliases, priority /
status validation).  Uses INSERT OR IGNORE on a natural-key so re-running is
safe and idempotent.

Usage:
    python backend/import_historical.py
    # or from inside the backend/ directory:
    python import_historical.py
"""

import os
import sqlite3
import csv
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CSV_PATH    = os.path.join(PROJECT_DIR, "datasets", "tickets_historical.csv")
DB_PATH     = os.path.join(BASE_DIR, "helpdesk.db")

# ── Same category map as the ETL pipeline ─────────────────────────────────────
CATEGORY_MAP = {
    "vpn":                  "VPN Issue",
    "vpn issue":            "VPN Issue",
    "vpn problem":          "VPN Issue",
    "pwd reset":            "Password Reset",
    "password reset":       "Password Reset",
    "password_reset":       "Password Reset",
    "software install":     "Software Installation",
    "sw installation":      "Software Installation",
    "software installation":"Software Installation",
    "laptop problem":       "Laptop Issue",
    "laptop issue":         "Laptop Issue",
    "email problem":        "Email Access",
    "email access":         "Email Access",
    "network issue":        "Network Connectivity",
    "network connectivity": "Network Connectivity",
    "network problem":      "Network Connectivity",
    "hw request":           "Hardware Request",
    "hardware req":         "Hardware Request",
    "hardware request":     "Hardware Request",
}

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES   = {"Open", "In Progress", "Resolved", "Closed"}


def normalise_category(raw: str) -> str:
    key = raw.strip().lower()
    return CATEGORY_MAP.get(key, raw.strip().title())


def normalise_priority(raw: str) -> str:
    val = raw.strip().title()
    return val if val in VALID_PRIORITIES else "Medium"


def normalise_status(raw: str) -> str:
    val = raw.strip().title()
    return val if val in VALID_STATUSES else "Open"


def parse_dt(val: str) -> str:
    """Return an ISO datetime string, or now() if blank/unparseable."""
    if not val or val.strip() == "":
        return datetime.utcnow().isoformat(sep=" ")
    try:
        # Accept 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(val.strip(), fmt).isoformat(sep=" ")
            except ValueError:
                continue
    except Exception:
        pass
    return datetime.utcnow().isoformat(sep=" ")


def main():
    print("=" * 60)
    print("  Helpdesk Historical Import")
    print(f"  CSV  : {CSV_PATH}")
    print(f"  DB   : {DB_PATH}")
    print("=" * 60)

    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] CSV not found: {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Add a unique index on the natural key so INSERT OR IGNORE deduplicates
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tickets_natural_key
        ON tickets(employee_name, issue_category, description, created_at)
    """)
    conn.commit()

    inserted = skipped = errors = 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows missing required fields
            emp  = (row.get("employee_name") or "").strip()
            desc = (row.get("description")   or "").strip()
            if not emp or not desc:
                skipped += 1
                continue

            category   = normalise_category(row.get("issue_category", ""))
            priority   = normalise_priority(row.get("priority",       ""))
            status     = normalise_status  (row.get("status",         ""))
            dept       = (row.get("department") or "Unknown").strip().title()
            notes      = (row.get("resolution_notes") or "").strip()
            created_at = parse_dt(row.get("created_at",  ""))
            # resolved_at from CSV → updated_at in live DB
            resolved   = row.get("resolved_at", "").strip()
            updated_at = parse_dt(resolved) if resolved else created_at

            try:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO tickets
                        (employee_name, department, issue_category,
                         description, priority, status, resolution_notes,
                         created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (emp, dept, category, desc, priority, status,
                     notes, created_at, updated_at),
                )
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  [WARN] Row skipped – {e}")
                errors += 1

    conn.commit()

    # Report
    cur.execute("SELECT COUNT(*) FROM tickets")
    total = cur.fetchone()[0]
    conn.close()

    print(f"\n  Inserted : {inserted}")
    print(f"  Skipped  : {skipped}  (already existed or blank)")
    print(f"  Errors   : {errors}")
    print(f"  Total in DB now : {total}")
    print("\n  Done – refresh 'All Tickets' in the browser.")
    print("=" * 60)


if __name__ == "__main__":
    main()
