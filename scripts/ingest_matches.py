# scripts/ingest_matches.py
import os, time, json
from tqdm import tqdm
from riotwatcher import LolWatcher, ApiError
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
watcher = LolWatcher(API_KEY)

# platform for league-v4; routing for match-v5
REGIONS = [
    {"name": "na",  "platform": "na1",  "routing": "AMERICAS"},
    {"name": "euw", "platform": "euw1", "routing": "EUROPE"},
    {"name": "kr",  "platform": "kr",   "routing": "ASIA"},
]

RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

def safe_fetch(fn, *args, retries=3, **kwargs):
    for i in range(retries):
        try:
            return fn(*args, **kwargs)
        except ApiError as e:
            code = getattr(e.response, "status_code", None)
            print(f"API error {code}: {e}")
            if code == 429:
                time.sleep(120)
            elif code in {500, 502, 503, 504}:
                time.sleep(10)
            else:
                return None
        except Exception as ex:
            print("Error:", ex)
            return None
    return None

def get_league_entries(platform: str):
    """Fetch Challenger + Grandmaster entries for a platform shard."""
    entries = []

    # Correct method names for riotwatcher 3.3.1:
    ch = safe_fetch(watcher.league.challenger_by_queue, platform, "RANKED_SOLO_5x5")
    if ch and "entries" in ch:
        entries.extend(ch["entries"])

    gm = safe_fetch(watcher.league.grandmaster_by_queue, platform, "RANKED_SOLO_5x5")
    if gm and "entries" in gm:
        entries.extend(gm["entries"])

    return entries

def get_match_ids_for_puuid(routing: str, puuid: str, count=20):
    return safe_fetch(watcher.match.matchlist_by_puuid, routing, puuid, count=count) or []

def fetch_and_save_match(routing: str, match_id: str, region_tag: str):
    m = safe_fetch(watcher.match.by_id, routing, match_id)
    if not m:
        return False
    out = os.path.join(RAW_DIR, f"{region_tag}_{match_id}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(m, f)
    return True

def main(max_per_summoner=5):
    if not API_KEY:
        print("No RIOT_API_KEY found. Put it in .env")
        return

    for r in REGIONS:
        print(f"Processing {r['name']} (platform={r['platform']} routing={r['routing']})")

        # Get league entries (each entry now includes a PUUID)
        entries = get_league_entries(r["platform"])
        puuids = [e["puuid"] for e in entries if isinstance(e, dict) and e.get("puuid")]
        puuids = list(dict.fromkeys(puuids))  # dedupe while preserving order
        print(f"PUUIDs collected: {len(puuids)}")

        saved = 0
        # cap the number of PUUIDs on first run to be gentle
        for puuid in tqdm(puuids[:300], desc=f"{r['name']} matchlists"):
            mids = get_match_ids_for_puuid(r["routing"], puuid, count=max_per_summoner)
            for mid in mids:
                if fetch_and_save_match(r["routing"], mid, r["name"]):
                    saved += 1
            time.sleep(1.2)  # small delay to be nice to rate limits
        print(f"Saved {saved} matches for {r['name']}")

if __name__ == "__main__":
    main(max_per_summoner=5)
