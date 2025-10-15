# scripts/ingest_matches.py
import time, json, os
from riotwatcher import LolWatcher, ApiError
from config import RIOT_API_KEY, REGIONS, RAW_DIR
from tqdm import tqdm

watcher = LolWatcher(RIOT_API_KEY)

# queues
QUEUE = "RANKED_SOLO_5x5"

def get_league_entries(platform):
    # get challenger + grandmaster entries
    res = []
    try:
        ch = watcher.league.challenger_by_queue(platform, QUEUE)
        res += ch.get("entries", [])
    except ApiError as e:
        print("Challenger fetch error", e)
    try:
        gm = watcher.league.grandmaster_by_queue(platform, QUEUE)
        res += gm.get("entries", [])
    except ApiError as e:
        print("Grandmaster fetch error", e)
    return res

def safe_fetch(fn, *args, retries=5, wait=1, **kwargs):
    for i in range(retries):
        try:
            return fn(*args, **kwargs)
        except ApiError as e:
            print("API error", e)
            time.sleep(wait * (i+1))
    raise RuntimeError("Max retries exceeded")

def main(max_per_summoner=20):
    seen_matches = set()
    for region_key, region_cfg in REGIONS.items():
        platform = region_cfg["platform"]
        match_routing = region_cfg["match_routing"]
        print("Processing region", region_key)
        entries = get_league_entries(platform)
        # dedupe summoners by puuid
        puuids = []
        for e in entries:
             # make sure it's a dict and the key exists
            if not isinstance(e, dict):
            continue
            summ_id = e.get("summonerId")
            if not summ_id:
                # log what we do have so we can debug, then skip
                print("entry missing summonerId; keys=", list(e.keys()))
                continue
            try:
                summ = safe_fetch(watcher.summoner.by_id, platform, summ_id)
                if summ and "puuid" in summ:
                    puuids.append(summ["puuid"])
            except Exception as ex:
            print("summoner error", ex)
        for puuid in tqdm(puuids):
            try:
                ids = safe_fetch(watcher.match.matchlist_by_puuid, match_routing, puuid, start=0, count=max_per_summoner)
                for mid in ids:
                    if mid in seen_matches:
                        continue
                    seen_matches.add(mid)
                    # fetch match details
                    try:
                        m = safe_fetch(watcher.match.by_id, match_routing, mid)
                        # save
                        fname = os.path.join(RAW_DIR, f"{region_key}_{mid}.json")
                        with open(fname, "w", encoding="utf8") as f:
                            json.dump(m, f)
                    except Exception as ex:
                        print("match fetch error", ex)
                time.sleep(1.2)  # crude rate control
            except Exception as ex:
                print("matchlist fetch error", ex)

if __name__ == "__main__":
    main()

