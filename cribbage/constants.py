import os
from dotenv import load_dotenv

load_dotenv(override=True) 

DB_PATH = os.getenv("DB_PATH", "C:/Users/johnm/ccode/crib_engine/crib_cache.db")

if DB_PATH is None:
    raise ValueError("db path not specified. Needed for hard player")