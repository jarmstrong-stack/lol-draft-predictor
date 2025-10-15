# scripts/gui_inference.py
import json
import os
from pathlib import Path

import streamlit as st

# project imports
import sys, os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.inference import predict_rf

ROOT = Path(__file__).resolve().parents[1]
CHAMP_INDEX = ROOT / "data" / "processed" / "champ_index.json"
MODEL_WORLD = ROOT / "models" / "rf_ensemble_world.joblib"
MODEL_BASE = ROOT / "models" / "rf_base.joblib"

@st.cache_resource
def load_champion_list():
    with open(CHAMP_INDEX, "r", encoding="utf-8") as f:
        idx = json.load(f)
    # champion_index.json is { "Aatrox": {...}, ... }
    return sorted(list(idx.keys()))

@st.cache_resource
def pick_model_path():
    if MODEL_WORLD.exists():
        return str(MODEL_WORLD)
    if MODEL_BASE.exists():
        return str(MODEL_BASE)
    return None

ALL_CHAMPS = load_champion_list()
MODEL_PATH = pick_model_path()

st.set_page_config(page_title="LoL Draft Predictor", page_icon="🧠", layout="centered")
st.title("🧠 LoL Draft Predictor (with autocomplete)")

if MODEL_PATH is None:
    st.error("No model found. Train a model first (rf_base.joblib or rf_ensemble_world.joblib).")
    st.stop()

st.caption(f"Using model: `{Path(MODEL_PATH).name}`")
st.divider()

col1, col2 = st.columns(2)
with col1:
    blue = st.multiselect("Blue picks (up to 5)", options=ALL_CHAMPS, max_selections=5, key="blue")
with col2:
    red = st.multiselect("Red picks (up to 5)", options=ALL_CHAMPS, max_selections=5, key="red")

# normalize (strip whitespace etc.)
blue = [c.strip() for c in blue if c and c.strip()]
red  = [c.strip() for c in red if c and c.strip()]

used = set([c.lower() for c in blue + red])
remaining = [c for c in ALL_CHAMPS if c.lower() not in used]

st.write(f"🧮 Current picks — Blue: {len(blue)}/5, Red: {len(red)}/5")

# --- prediction block
st.subheader("Prediction")
try:
    p_blue = predict_rf(blue, red, model_path=MODEL_PATH)
    st.metric("P(Blue wins)", f"{p_blue*100:.1f}%")
except Exception as e:
    st.info("Prediction will work best with valid champs; if the model needs full 5v5, finish picks first.")
    st.code(str(e))

st.divider()

# --- suggestion block
st.subheader("Suggest next pick")
side = st.radio("Who picks next?", ["blue", "red"], horizontal=True)
top_n = st.slider("How many suggestions?", 5, 30, 10)

def suggest_next(side: str, blue_list, red_list, candidates, topk=10):
    base = predict_rf(blue_list, red_list, model_path=MODEL_PATH)
    out = []
    for c in candidates:
        if side == "blue":
            nb, nr = blue_list + [c], red_list
        else:
            nb, nr = blue_list, red_list + [c]
        if len(nb) > 5 or len(nr) > 5:
            continue
        try:
            p = predict_rf(nb, nr, model_path=MODEL_PATH)
        except Exception:
            continue
        # delta for the *side to move*
        delta = (p - base) if side == "blue" else ((1 - p) - (1 - base))
        out.append((c, p, delta))
    # sort by delta, tie-break by probability for the relevant side
    out.sort(key=lambda x: (x[2], x[1] if side == "blue" else (1 - x[1])), reverse=True)
    return base, out[:topk]

if len(blue) <= 5 and len(red) <= 5:
    base_p, picks = suggest_next(side, blue, red, remaining, top_n)
    st.caption(f"Current P(Blue wins): {base_p:.4f}")
    if picks:
        st.write(f"Top {len(picks)} suggestions for **{side}**:")
        for c, p, d in picks:
            if side == "blue":
                st.write(f"- **{c}** → new P(Blue) = {p:.4f}  (Δ for Blue: {'+' if d>=0 else ''}{d:.4f})")
            else:
                st.write(f"- **{c}** → new P(Blue) = {p:.4f}  (Δ for Red: {'+' if d>=0 else ''}{d:.4f})")
    else:
        st.info("No valid suggestions (maybe you already have 5 champs on that side).")

st.divider()
st.caption("Tip: start typing a champion name in the boxes above to autocomplete. Model prefers Worlds-tuned ensemble if present.")
