import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True) 

DB_PATH = os.getenv("DB_PATH", "C:/Users/johnm/ccode/crib_engine/crib_cache.db")
HAND_CRIB_DB_PATH = os.getenv(
    "HAND_CRIB_DB_PATH",
    str((Path(__file__).resolve().parents[1] / "data" / "hand_crib_stats.sqlite")),
)

if DB_PATH is None:
    raise ValueError("db path not specified. Needed for hard player")
