from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"text", "intent"}

def load_training_data(path):
    df = pd.read_csv(path).copy()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Training data is missing columns: {sorted(missing)}")
    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df["intent"] = df["intent"].fillna("").astype(str).str.strip()
    df = df[(df["text"] != "") & (df["intent"] != "")]
    df = df.drop_duplicates(subset=["text", "intent"]).reset_index(drop=True)
    if df["intent"].nunique() < 2:
        raise ValueError("Training data must contain at least two intent labels.")
    return df
