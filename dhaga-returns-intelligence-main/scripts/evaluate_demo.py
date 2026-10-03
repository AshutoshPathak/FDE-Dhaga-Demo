from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from src.data import clean_input, merge_predictions
from src.demo_classifier import classify_dataframe
from src.evaluation import evaluate

sample = ROOT / "data" / "dhaga_returns_sample_300.csv"
labeled = ROOT / "data" / "dhaga_returns_sample_300_labeled.csv"
df = clean_input(pd.read_csv(sample))
result = merge_predictions(df, classify_dataframe(df))
print(evaluate(result, str(labeled)))
