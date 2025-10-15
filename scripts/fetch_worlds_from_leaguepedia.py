# scripts/fetch_worlds_from_leaguepedia.py
import csv
import json
import time
import argparse
import requests

API = "https://lol.fandom.com/api.php"

# Cargo fields we need:
FIELDS = [
    "MatchScheduleGame.GameId=gameid",
    "MatchScheduleGame.Patch=patch",
    "MatchScheduleGame.Winner=winner",            # usually team name; sometimes "1"/"2"
    "MatchScheduleGame.Team1=team1",
    "MatchScheduleGame.Team2=team2",
    "MatchScheduleGame.Team1Side=team1side",      # "Blue" or "Red"
    "PicksAndBansS7.Blue1=blue1",
    "PicksAndBansS7.Blue2=blue2",
    "PicksAndBansS7.Blue3=blue3",
    "PicksAndBansS7.Blue4=blue4",
    "PicksAndBansS7.Blue5=blue5",
    "PicksAndBansS7.Red1=red1",
    "PicksAndBansS7.Red2=red2",
    "PicksAndBansS7.Red3=red3",
    "PicksAndBansS7.Red4=red4",
    "PicksAndBansS7.Red5=red5",
]

def cargo_query(tournament, where_extra=None, limit=500, sleep=0.25):
    """
    Generator yielding rows from Leaguepedia Cargo API for a given tournament name.
    """
    offset = 0
    while True:
        where = f'MatchScheduleGame.Tournament="{tournament}"'
        if where_extra:
            where += f" AND ({where_extra})"

        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": "MatchScheduleGame,PicksAndBansS7",
            "join_on": "MatchScheduleGame.GameId=PicksAndBansS7.GameId",
            "fields": ",".join(FIELDS),
            "where": where,
            "limit": str(limit),
            "offset": str(offset),
        }
        r = requests.get(API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        rows = data.get("cargoquery", [])
        if not rows:
            break

        for item in rows:
            yield item.get("title", {})

        offset += limit
        time.sleep(sleep)  # be nice

def normalize_winner_side(rec):
    """
    Return 'Blue' or 'Red' as the winner based on MatchScheduleGame.Winner.
    Winner can be team name, or '1'/'2' (team index).
    We can infer side via Team1Side + Winner value.
    """
    winner = (rec.get("winner") or "").strip()
    team1 = (rec.get("team1") or "").strip()
    team2 = (rec.get("team2") or "").strip()
    team1side = (rec.get("team1side") or "").strip()  # 'Blue' or 'Red'

    if not team1side:
        return None  # can't determine

    # If Winner is '1' or '2'
    if winner in ("1", "2"):
        if winner == "1":
            return team1side
        else:
            return "Red" if team1side == "Blue" else "Blue"

    # If Winner equals team name
    if winner and (winner == team1 or winner == team2):
        if winner == team1:
            return team1side
        else:
            return "Red" if team1side == "Blue" else "Blue"

    # Fallback: unknown
    return None

def row_to_output(rec):
    # champion lists (already labeled blue/red in PicksAndBansS7)
    blue = [rec.get(f"blue{i}") for i in range(1,6)]
    red  = [rec.get(f"red{i}")  for i in range(1,6)]
    blue = [c for c in blue if c]
    red  = [c for c in red if c]

    # patch shorten to e.g. '25.20' if '25.20.xxx'
    patch = (rec.get("patch") or "").strip()
    if patch and patch.count(".") >= 2:
        parts = patch.split(".")
        patch = ".".join(parts[:2])

    winner_side = normalize_winner_side(rec)
    if not winner_side:
        return None

    return {
        "match_id": rec.get("gameid"),
        "patch": patch,
        "blue_champs": json.dumps(blue, ensure_ascii=False),
        "red_champs": json.dumps(red, ensure_ascii=False),
        "winner": winner_side,
    }

def main():
    ap = argparse.ArgumentParser(description="Fetch Worlds matches from Leaguepedia into examples/worlds_matches.csv")
    ap.add_argument("--tournament", default="World Championship 2025",
                    help="Exact Tournament name on Leaguepedia (e.g., 'World Championship 2025')")
    ap.add_argument("--outfile", default="examples/worlds_matches.csv",
                    help="Path to write CSV")
    ap.add_argument("--where-extra", default=None,
                    help="Extra WHERE clause, e.g. \"MatchScheduleGame.DateTime_UTC >= '2025-10-01'\"")
    args = ap.parse_args()

    out_rows = []
    for rec in cargo_query(args.tournament, args.where_extra):
        row = row_to_output(rec)
        if row and row["blue_champs"] != "[]" and row["red_champs"] != "[]":
            out_rows.append(row)

    # Deduplicate by match_id
    seen = set()
    dedup = []
    for r in out_rows:
        mid = r["match_id"]
        if mid in seen or not mid:
            continue
        seen.add(mid)
        dedup.append(r)

    # Write CSV
    os.makedirs(os.path.dirname(args.outfile), exist_ok=True)
    with open(args.outfile, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["match_id","patch","blue_champs","red_champs","winner"])
        w.writeheader()
        w.writerows(dedup)

    print(f"Wrote {len(dedup)} games to {args.outfile}")

if __name__ == "__main__":
    main()
