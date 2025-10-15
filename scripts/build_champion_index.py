# scripts/build_champion_index.py
import json, pandas as pd
from config import BASE_CSV, WORLDS_CSV, CHAMP_INDEX_PATH
from ast import literal_eval

def gather_champs():
    champions = set()
    for path in [BASE_CSV, WORLDS_CSV]:
        try:
            df = pd.read_csv(path)
        except:
            continue
        for col in ["blue_champs","red_champs"]:
            for s in df[col].dropna():
                champs = literal_eval(s)
                for c in champs:
                    champions.add(c)
    champ_list = sorted(list(champions))
    idx = {c:i for i,c in enumerate(champ_list)}
    with open(CHAMP_INDEX_PATH, "w", encoding="utf8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    print("Saved champ index", CHAMP_INDEX_PATH, "count=", len(idx))

if __name__ == "__main__":
    gather_champs()

