import os
import time
import json
from tqdm import tqdm
from riotwatcher import LolWatcher, ApiError
from dotenv import load_dotenv

# --- Load config and constants ---
load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")
REGIONS = ["na1", "euw1", "kr"]
RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# --- Setup watcher ---
watcher = LolWatcher(RIOT_API_KEY)

# --- Helper to safely call API endpoints ---
def safe_fetch(func, *args, retries=3, **kwargs):
    for _ in range(retries):
        try:
            return func(*args, **kwargs)
        except ApiError as err:
            if err.response.status_code == 429:
                print("Rate limited, sleeping 120s...")
                time.sleep(120)
            elif err.response.status_code in [500, 502, 503, 504]:
                print("Server error, retrying...")
                time.sleep(10)
            else:
                print(f"API error: {err}")
                return None
        except Exception as ex:
            print(f"Error: {ex}")
            return None
    return None

# --- Fetch Challenger + Grandmaster League entries ---
def get_league_entries(region):
    leagues = []
    for tier in ["challengerleagues", "grandmasterleagues"]:
        url_func = getattr(watcher.league, f"{tier}_by_queue")
        data = safe_fetch(url_func, region, "RANKED_SOLO_5x5")
        if data and "entries" in data:
            leagues.extend(data["entries"])
        else:
            print(f"⚠️ No data for {region} {tier}")
    return leagues

# --- Fetch matches for each puuid ---
def get_matches(region, puuid_list, max_per_summoner=10):
    all_matches = []
    for puuid in tqdm(puuid_list, desc=f"{region} matches"):
        matches = safe_fetch(
            watcher.match.matchlist_by_puuid, region, puuid, count=max_per_summoner
        )
        if not matches:
            continue
        for match_id in matches:
            match = safe_fetch(watcher.match.by_id, region, match_id)
            if match:
                all_matches.append(match)
                # Save incrementally
                out_path = os.path.join(RAW_DIR, f"{region}_{match_id}.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(match, f)
    return all_matches

# --- MAIN ---
def main(max_per_summoner=10):
    print("Starting ingestion...")
    for region in REGIONS:
        print(f"Processing region {region}")
        entries = get_league_entries(region)
        puuids = []

        for e in entries:
            # Riot API returns puuid directly in new versions
            if isinstance(e, dict) and e.get("puuid"):
                puuids.append(e["puuid"])
            else:
                print("entry missing puuid; keys=", list(e.keys()) if isinstance(e, dict) else type(e))

        puuids = list(set(puuids))  # deduplicate
        print(f"Collected {len(puuids)} unique PUUIDs from {region}")
        _ = get_matches(region, puuids, max_per_summoner=max_per_summoner)

if __name__ == "__main__":
    main(max_per_summoner=5)
