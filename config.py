# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")

# rest of your config below
REGIONS = {
    "na": {"platform": "na1", "match_routing": "AMERICAS"},
    "euw": {"platform": "euw1", "match_routing": "EUROPE"},
    "kr": {"platform": "kr", "match_routing": "ASIA"},
}

# Riot API
RIOT_API_KEY = os.getenv("RIOT_API_KEY", "RGAPI-REPLACE_WITH_YOUR_KEY")
REGIONS = {
    "na": {"platform": "na1", "match_routing": "AMERICAS"},
    "euw": {"platform": "euw1", "match_routing": "EUROPE"},
    "kr": {"platform": "kr", "match_routing": "ASIA"},
}
TARGET_PATCH = "25.20"  # change to the Worlds patch string format you need
DATA_DIR = "data"
RAW_DIR = f"{DATA_DIR}/raw"
PROCESSED_DIR = f"{DATA_DIR}/processed"
CHAMP_INDEX_PATH = f"{PROCESSED_DIR}/champ_index.json"
BASE_CSV = f"{PROCESSED_DIR}/base_matches.csv"
WORLDS_CSV = "examples/worlds_matches.csv"  # user-provided CSV of Worlds matches
MODEL_DIR = "models"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

