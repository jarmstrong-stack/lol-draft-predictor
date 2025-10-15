# src/inference.py
import joblib
import torch
import json
import numpy as np
from pathlib import Path
from config import MODEL_DIR, CHAMP_INDEX_PATH
from src.utils import champs_to_signed_vector, parse_champion_list

# Load champion index
with open(CHAMP_INDEX_PATH, "r", encoding="utf8") as f:
    CHAMP_TO_IDX = json.load(f)
NUM_CHAMPS = len(CHAMP_TO_IDX)


# -------------------------
# Random Forest Prediction
# -------------------------
def predict_rf(blue_champs, red_champs, model_path=None):
    """Predict which team wins using Random Forest model."""
    try:
        model_file = Path(model_path) if model_path else Path(MODEL_DIR) / "rf_ensemble_world.joblib"
        model = joblib.load(model_file)
    except Exception as e:
        raise RuntimeError(f"Could not load model: {e}")

    # Convert champions to signed vector (+1 for blue, -1 for red)
    try:
        v = champs_to_signed_vector(blue_champs, red_champs).reshape(1, -1)
    except Exception as e:
        raise RuntimeError(f"Vectorization failed: {e}")

    # Predict probabilities
    try:
        probs = model.predict_proba(v)[0]
        blue_prob = float(probs[1])  # assuming class 1 = Blue
        red_prob = float(probs[0])
    except Exception as e:
        raise RuntimeError(f"Prediction failed: {e}")

    winner = "Blue Side Wins" if blue_prob >= red_prob else "Red Side Wins"
    confidence = abs(blue_prob - red_prob)

    return {
        "prediction": winner,
        "blue_prob": round(blue_prob * 100, 2),
        "red_prob": round(red_prob * 100, 2),
        "confidence": round(confidence * 100, 2)
    }


# -------------------------
# Embedding Model Prediction
# -------------------------
class CompEmbedNet(torch.nn.Module):
    def __init__(self, num_champs, emb_dim=64):
        super().__init__()
        self.emb = torch.nn.Embedding(num_champs, emb_dim)
        self.fc = torch.nn.Linear(emb_dim * 10 + 1, 1)
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, blue_idx, red_idx, side_flag):
        b = self.emb(blue_idx).view(blue_idx.size(0), -1)
        r = self.emb(red_idx).view(red_idx.size(0), -1)
        x = torch.cat([b, r, side_flag.unsqueeze(1)], dim=1)
        return self.sigmoid(self.fc(x))


def predict_embed(blue_champs, red_champs, model=None, device=None):
    """Predict win chance using embedding neural network model."""
    if model is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = CompEmbedNet(NUM_CHAMPS, emb_dim=64).to(device)
        model.load_state_dict(torch.load(f"{MODEL_DIR}/embed_base.pt", map_location=device))
        model.eval()

    # Convert champ names to indices
    def to_idx_list(champs):
        out = [CHAMP_TO_IDX.get(c, 0) for c in champs]
        while len(out) < 5:
            out.append(0)
        return out[:5]

    b_idx = torch.tensor([to_idx_list(blue_champs)], dtype=torch.long)
    r_idx = torch.tensor([to_idx_list(red_champs)], dtype=torch.long)
    side_flag = torch.tensor([1.0])

    with torch.no_grad():
        pred = model(b_idx, r_idx, side_flag)
        blue_prob = float(pred.item())
        red_prob = 1 - blue_prob

    winner = "Blue Side Wins" if blue_prob >= red_prob else "Red Side Wins"
    confidence = abs(blue_prob - red_prob)

    return {
        "prediction": winner,
        "blue_prob": round(blue_prob * 100, 2),
        "red_prob": round(red_prob * 100, 2),
        "confidence": round(confidence * 100, 2)
    }


# -------------------------
# Quick manual test
# -------------------------
if __name__ == "__main__":
    blue = ["Aatrox", "Sejuani", "Azir", "Aphelios", "Rell"]
    red = ["Renekton", "Viego", "Ahri", "Xayah", "Rakan"]

    print("Random Forest Prediction:")
    print(predict_rf(blue, red))

    print("\nEmbedding Model Prediction:")
    print(predict_embed(blue, red))
