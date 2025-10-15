# src/fine_tune.py
import joblib, os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from src.preprocess import load_worlds_data, load_base_data
from config import MODEL_DIR

def fine_tune_rf():
    # load base model
    rf_path = os.path.join(MODEL_DIR, "rf_base.joblib")
    rf = joblib.load(rf_path)
    Xw, yw = load_worlds_data()
    if len(yw) < 10:
        print("Too few worlds matches to fine-tune reliably:", len(yw))
    # simple approach: continue training by fitting a small RF on worlds and ensemble
    rf_world = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    rf_world.fit(Xw, yw)
    # Save ensemble pair (base + world-specific)
    joblib.dump({"base": rf, "world": rf_world}, os.path.join(MODEL_DIR, "rf_ensemble_world.joblib"))
    print("Saved rf ensemble")

if __name__ == "__main__":
    fine_tune_rf()

