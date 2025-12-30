import os
from dotenv import load_dotenv

load_dotenv(override=True) 

DB_PATH = os.getenv("DB_PATH")

if DB_PATH is None:
    raise ValueError("db path not specified. Needed for hard player")