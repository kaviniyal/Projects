"""
ETL Package — Enterprise Knowledge Base Phase 2.

Modules:
  extract   — Read raw CSV/JSON datasets into Pandas DataFrames.
  transform — Clean, normalise, and enrich the raw data.
  load      — Upsert transformed data into the SQLite database.
  pipeline  — Orchestrator that runs Extract → Transform → Load.
  reports   — Generate analytics report CSVs from the loaded data.
"""
