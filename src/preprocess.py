# src/preprocess.py
import pandas as pd
import numpy as np
from src.utils import champs_to_signed_vector, parse_champion_list
from config import BASE_CSV, WORLDS_CSV
import joblib

def load_base_data():
    df = pd.read_csv(BASE_CSV)
    X = []
    y = []
    for _, row in df.iterrows():
        blue = parse_champion_list(row["blue_champs"])
        red = parse_champion_list(row["red_champs"])
        v = champs_to_signed_vector(blue, red)
        X.append(v)
        y.append(1 if row["winner"] == "Blue" else 0)
    X = np.vstack(X)
    y = np.array(y)
    return X, y

def load_worlds_data():
    df = pd.read_csv(WORLDS_CSV)
    X = []
    y = []
    for _, row in df.iterrows():
        blue = parse_champion_list(row["blue_champs"])
        red = parse_champion_list(row["red_champs"])
        v = champs_to_signed_vector(blue, red)
        X.append(v)
        y.append(1 if row["winner"] == "Blue" else 0)
    X = np.vstack(X)
    y = np.array(y)
    return X, y

