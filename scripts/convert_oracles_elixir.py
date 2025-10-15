# scripts/convert_oracles_elixir.py
import argparse
import json
import os
import pandas as pd

OUT_DEFAULT = "examples/worlds_matches.csv"

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make Oracle's Elixir columns consistent:
    expect: gameid, patch, side, champion, result, league (optional)
    """
    cols = {c.lower(): c for c in df.columns}

    # Map common variants → canonical
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
        raise KeyError(f"Missing required column; tried {names}")

    mapping = {
        "gameid": pick("gameid", "game_id", "game"),
        "patch":  pick("patch", "gamepatch", "patchno"),
        "side":   pick("side", "teamside"),
        "champion": pick("champion", "champ"),
        "result": pick("result", "win", "outcome"),
    }

    # Optional / nice-to-have
    league_col = cols.get("league") or cols.get("tournament") or cols.get("event") or None
    if league_col: mapping["league"] = league_col

    # Rename into canonical
    df = df.rename(columns={v:k for k,v in mapping.items()})
    return df

def result_to_label(series):
    """Return 'Win'/'Loss' per row regardless of encoding."""
    vals = []
    for v in series:
        if isinstance(v, str):
            s = v.strip().lower()
            if s in ("win", "w", "true", "1"): vals.append("Win")
            elif s in ("loss", "l", "false", "0"): vals.append("Loss")
            else: vals.append(v)
        elif isinstance(v, (int, float)):
            vals.append("Win" if v == 1 else "Loss")
        else:
            vals.append(v)
    return pd.Series(vals)

def main():
    ap = argparse.ArgumentParser(description="Convert Oracle's Elixir match CSV → worlds_matches.csv format.")
    ap.add_argument("--infile", required=True, help="Path to Oracle's Elixir match CSV (2025).")
    ap.add_argument("--outfile", default=OUT_DEFAULT, help=f"Output CSV (default: {OUT_DEFAULT})")
    ap.add_argument("--patch-prefix", default=None, help='Keep rows where patch starts with this (e.g. "25.20").')
    ap.add_argument("--league-like", default=None, help='Substring filter on league/tournament name (e.g. "World").')
    ap.add_argument("--require-5", action="store_true", help="Drop games that don't have exactly 5 champs per side.")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.outfile), exist_ok=True)

    df = pd.read_csv(args.infile, low_memory=False)
    df = normalize_columns(df)
    # Normalize result
    df["result"] = result_to_label(df["result"])

    # Optional filters
    if args.patch_prefix:
        df = df[df["patch"].astype(str).str.startswith(args.patch_prefix)]

    if "league" in df.columns and args.league_like:
        df = df[df["league"].astype(str).str.contains(args.league_like, case=False, na=False)]

    # Keep needed columns only
    keep = ["gameid","patch","side","champion","result"]
    df = df[keep]

    # Build per-game records
    rows = []
    for gid, g in df.groupby("gameid", sort=False):
        # sides are "Blue"/"Red" in OE; make robust just in case
        def side_mask(side_name):
            return g["side"].astype(str).str.lower().str.startswith(side_name)

        blue = g.loc[side_mask("blue"), "champion"].dropna().tolist()
        red  = g.loc[side_mask("red"),  "champion"].dropna().tolist()

        if args.require_5 and (len(blue) != 5 or len(red) != 5):
            continue

        # winner: take unique result for Blue side
        blue_res = g.loc[side_mask("blue"), "result"].dropna().unique().tolist()
        winner = None
        if any(x == "Win" for x in blue_res):
            winner = "Blue"
        elif any(x == "Loss" for x in blue_res):
            winner = "Red"

        # fallbacks if blue result missing (very rare):
        if not winner:
            # try infer by which side has any 'Win'
            red_res = g.loc[side_mask("red"), "result"].dropna().unique().tolist()
            if any(x == "Win" for x in red_res):
                winner = "Red"
            elif any(x == "Loss" for x in red_res):
                winner = "Blue"

        # patch: pick most common in group
        patch = (
            g["patch"].dropna().astype(str).mode().iloc[0]
            if not g["patch"].dropna().empty else ""
        )
        # shorten 25.20.x to 25.20
        if patch.count(".") >= 2:
            patch = ".".join(patch.split(".")[:2])

        if not blue or not red or not winner:
            continue

        rows.append({
            "match_id": gid,
            "patch": patch,
            "blue_champs": json.dumps(blue, ensure_ascii=False),
            "red_champs": json.dumps(red, ensure_ascii=False),
            "winner": winner
        })

    out = pd.DataFrame(rows).drop_duplicates(subset=["match_id"])
    out.to_csv(args.outfile, index=False)
    print(f"Wrote {len(out)} games to {args.outfile}")

if __name__ == "__main__":
    main()
