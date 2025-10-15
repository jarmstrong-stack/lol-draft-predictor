# src/utils.py
import json, numpy as np
from ast import literal_eval
from config import CHAMP_INDEX_PATH
with open(CHAMP_INDEX_PATH, "r", encoding="utf8") as f:
    CHAMP_TO_IDX = json.load(f)
IDX_TO_CHAMP = {int(v):k for k,v in CHAMP_TO_IDX.items()}

def champs_to_signed_vector(blue, red):
    C = len(CHAMP_TO_IDX)
    v = np.zeros(C, dtype=np.float32)
    for c in blue:
        if c in CHAMP_TO_IDX:
            v[CHAMP_TO_IDX[c]] += 1.0
    for c in red:
        if c in CHAMP_TO_IDX:
            v[CHAMP_TO_IDX[c]] -= 1.0
    return v

def parse_champion_list(s):
    if isinstance(s, list):
        return s
    try:
        return literal_eval(s)
    except:
        return []

