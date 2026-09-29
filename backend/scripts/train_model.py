from pathlib import Path
import sys
BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))
from joblib import dump
from backend.ml.pipeline import CareRouter, build_pipeline
from backend.ml.preprocess import load_training_data

BASE = Path(__file__).resolve().parents[1]
data_path = BASE / "data" / "symptom_training_data.csv"
out = BASE / "models" / "symptom_router.joblib"
df = load_training_data(data_path)
model = build_pipeline(); model.fit(df["text"], df["intent"])
out.parent.mkdir(parents=True, exist_ok=True); dump(model, out)
print(f"Saved {out} | {len(df)} validated training examples | {df['intent'].nunique()} intents")
