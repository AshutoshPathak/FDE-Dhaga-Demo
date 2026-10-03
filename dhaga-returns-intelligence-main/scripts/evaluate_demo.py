import argparse
import json
from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from src.data import clean_input, merge_predictions
from src.demo_classifier import classify_dataframe
from src.evaluation import evaluate

parser = argparse.ArgumentParser(description="Evaluate an exported Dhaga classified CSV against held-back labels.")
parser.add_argument("predicted_csv", nargs="?", help="CSV exported by the app after a live run")
parser.add_argument("--labels", default=ROOT / "data" / "dhaga_returns_sample_300_labeled.csv", help="Held-back labels CSV")
parser.add_argument("--demo", action="store_true", help="Evaluate the deterministic demo classifier instead of an exported live run")
args = parser.parse_args()

if args.demo:
    sample = ROOT / "data" / "dhaga_returns_sample_300.csv"
    predicted = merge_predictions(clean_input(pd.read_csv(sample)), classify_dataframe(clean_input(pd.read_csv(sample))))
elif args.predicted_csv:
    predicted = pd.read_csv(args.predicted_csv)
else:
    parser.error("Provide an exported CSV path, or use --demo.")

print(json.dumps(evaluate(predicted, str(args.labels)), indent=2))
