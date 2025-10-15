# src/inference.py
import joblib, torch, json, numpy as np
from config import MODEL_DIR, CHAMP_INDEX_PATH
from src.utils import champs_to_signed_vector, parse_champion_list
with open(CHAMP_INDEX_PATH, "r", encoding="utf8") as f:
    CHAMP_TO_IDX = json.load(f)
NUM_CHAMPS = len(CHAMP_TO_IDX)

def predict_rf(blue_champs, red_champs, model_path=None):
    if model is None:
        model = joblib.load(f"{MODEL_DIR}/rf_base.joblib")
    v = champs_to_signed_vector(blue_champs, red_champs).reshape(1,-1)
    return model.predict_proba(v)[0,1]

def predict_embed(blue_champs, red_champs, model=None, device=None):
    if model is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = CompEmbedNet(NUM_CHAMPS, emb_dim=64).to(device)
        model.load_state_dict(torch.load(f"{MODEL_DIR}/embed_base.pt", map_location=device))
        model.eval()
    # convert champ names to indices
    def to_idx_list(champs):
        out = [CHAMP_TO_IDX.get(c,0) for c in champs]
        while len(out) < 5:
            out.append(0)
        return out[:5]
    b_idx = torch.tensor([to_idx_list(blue_champs)], dtype=torch.long)
    r_idx = torch.tensor([to_idx_list(red_champs)], dtype=torch.long)
    side_flag = torch.tensor([1.0])
    with torch.no_grad():
        pred = model(b_idx, r_idx, side_flag)
    return float(pred.item())

if __name__ == "__main__":
    # quick example
    blue = ["Aatrox","Sejuani","Azir","Aphelios","Rell"]
    red = ["Renekton","Viego","Ahri","Xayah","Rakan"]
    print("RF prob Blue:", predict_rf(blue, red))
    print("Embed prob Blue:", predict_embed(blue, red))

