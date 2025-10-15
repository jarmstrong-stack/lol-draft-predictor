# src/train_base.py
import joblib, os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from src.preprocess import load_base_data
from config import MODEL_DIR

def train_rf():
    X, y = load_base_data()
    # simple time-aware split: use last 20% as holdout (if data ordered)
    split = int(len(X) * 0.8)
    X_train, X_hold = X[:split], X[split:]
    y_train, y_hold = y[:split], y[split:]
    rf = RandomForestClassifier(n_estimators=300, max_depth=12, n_jobs=-1, random_state=42)
    print("Training RF on", X_train.shape)
    rf.fit(X_train, y_train)
    hold_acc = rf.score(X_hold, y_hold)
    cv = cross_val_score(rf, X_train, y_train, cv=5, n_jobs=-1)
    print("Holdout accuracy:", hold_acc)
    print("CV mean:", cv.mean(), "std:", cv.std())
    path = os.path.join(MODEL_DIR, "rf_base.joblib")
    joblib.dump(rf, path)
    print("Saved RF to", path)
    return rf

if __name__ == "__main__":
    train_rf()

