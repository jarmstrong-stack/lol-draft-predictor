# scripts/convert_raw_to_csv.py
import json, os, glob, csv
from config import RAW_DIR, PROCESSED_DIR, BASE_CSV, TARGET_PATCH
from tqdm import tqdm

def extract_champs_from_match(m):
    info = m.get("info", {})
    # check queueId
    if info.get("queueId") != 420:
        return None
    # patch in gameVersion e.g. "25.20.123"
    gv = info.get("gameVersion", "")
    version_short = ".".join(gv.split(".")[:2])
    if version_short != TARGET_PATCH:
        return None
    participants = info.get("participants", [])
    blue = []
    red = []
    for p in participants:
        champ = p.get("championName")
        team = p.get("teamId")
        if team == 100:
            blue.append(champ)
        else:
            red.append(champ)
    # winner: find team win boolean
    teams = info.get("teams", [])
    winner = None
    for t in teams:
        if t.get("teamId") == 100:
            winner = "Blue" if t.get("win") else "Red"
            break
    return {
        "match_id": m.get("metadata", {}).get("matchId"),
        "patch": version_short,
        "blue_champs": json.dumps(blue),
        "red_champs": json.dumps(red),
        "winner": winner
    }

def main():
    files = glob.glob(os.path.join(RAW_DIR, "*.json"))
    outrows = []
    for f in tqdm(files):
        try:
            with open(f, "r", encoding="utf8") as fh:
                m = json.load(fh)
            row = extract_champs_from_match(m)
            if row:
                outrows.append(row)
        except Exception as ex:
            print("parse error", f, ex)
    # dedupe by match_id
    seen = set()
    dedup = []
    for r in outrows:
        mid = r["match_id"]
        if mid in seen:
            continue
        seen.add(mid)
        dedup.append(r)
    # write CSV
    with open(BASE_CSV, "w", newline="", encoding="utf8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["match_id","patch","blue_champs","red_champs","winner"])
        writer.writeheader()
        for r in dedup:
            writer.writerow(r)
    print("Wrote", BASE_CSV, "rows:", len(dedup))

if __name__ == "__main__":
    main()

