"""Build a small SQLite DB with hand1/crib1 tables for HardPlayer."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from cribbage.constants import DB_PATH, HAND_CRIB_DB_PATH


def _copy_table(src: sqlite3.Connection, dst: sqlite3.Connection, table_name: str) -> None:
    dst.execute(f"DROP TABLE IF EXISTS {table_name}")
    create_sql = src.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if create_sql is None or create_sql[0] is None:
        raise SystemExit(f"Missing table {table_name} in source DB.")
    dst.execute(create_sql[0])
    rows = src.execute(f"SELECT * FROM {table_name}").fetchall()
    if rows:
        placeholders = ",".join(["?"] * len(rows[0]))
        dst.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
    dst.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=str, default=DB_PATH, help="Source DB with hand1/crib1 tables.")
    ap.add_argument("--dst", type=str, default=HAND_CRIB_DB_PATH, help="Output DB path.")
    args = ap.parse_args()

    src_path = Path(args.src)
    if not src_path.exists():
        raise SystemExit(f"Source DB does not exist: {src_path}")

    dst_path = Path(args.dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(str(src_path))
    dst = sqlite3.connect(str(dst_path))
    try:
        _copy_table(src, dst, "hand1")
        _copy_table(src, dst, "crib1")
    finally:
        src.close()
        dst.close()

    print(f"Wrote {dst_path}")


if __name__ == "__main__":
    main()
