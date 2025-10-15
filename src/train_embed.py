# src/train_embed.py
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import json
from config import CHAMP_INDEX_PATH, MODEL_DIR
from preprocess import load_base_data
import numpy as np
from src.utils import parse_champion_list
import joblib

# We will convert each row's blue & red champion lists to indices
with open(CHAMP_INDEX_PATH, "r", encoding="utf8") as f:
    CHAMP_TO_IDX = json.load(f)
NUM_CHAMPS = len(CHAMP_TO_IDX)

class CompDataset(Dataset):
    def __init__(self, csv_path):
        X, y = load_base_data()
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        v = self.X[idx]  # signed vector length C
        # recover blue and red indices (we stored as signed)
        blue_idx = np.where(v > 0)[0].astype(np.int64)
        red_idx = np.where(v < 0)[0].astype(np.int64)
        # pad/trim to exactly 5 champs for each side (common in practice)
        def pad_to_five(arr):
            a = arr.tolist()
            while len(a) < 5:
                a.append(0)
            return a[:5]
        blue_idx = pad_to_five(blue_idx)
        red_idx = pad_to_five(red_idx)
        return torch.tensor(blue_idx, dtype=torch.long), torch.tensor(red_idx, dtype=torch.long), torch.tensor(self.y[idx], dtype=torch.float32)

class CompEmbedNet(nn.Module):
    def __init__(self, num_champs, emb_dim=64):
        super().__init__()
        self.embedding = nn.Embedding(num_champs, emb_dim)
        self.fc = nn.Sequential(
            nn.Linear(emb_dim*2 + 1, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, blue_idx, red_idx, side_flag):
        # blue_idx, red_idx: (batch,5)
        be = self.embedding(blue_idx).mean(dim=1)
        re = self.embedding(red_idx).mean(dim=1)
        x = torch.cat([be, re, side_flag.unsqueeze(1).float()], dim=1)
        return self.fc(x).squeeze(1)

def train_embed(epochs=12, batch_size=256, lr=1e-3):
    ds = CompDataset(None)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CompEmbedNet(NUM_CHAMPS, emb_dim=64).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCELoss()
    for ep in range(epochs):
        model.train()
        total_loss = 0.0
        for blue_idx, red_idx, label in loader:
            blue_idx = blue_idx.to(device)
            red_idx = red_idx.to(device)
            label = label.to(device)
            side_flag = torch.ones(label.size(0), dtype=torch.float32).to(device)  # always treat Blue as focal; adjust if you include side features
            pred = model(blue_idx, red_idx, side_flag)
            loss = loss_fn(pred, label)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item() * label.size(0)
        print(f"Epoch {ep} loss {total_loss/len(ds):.4f}")
    torch.save(model.state_dict(), f"{MODEL_DIR}/embed_base.pt")
    print("Saved embedding model")
    return model

if __name__ == "__main__":
    train_embed()

