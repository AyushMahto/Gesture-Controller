"""Evaluate manually labelled gesture samples; predictions must be supplied independently."""
import argparse
import csv
from pathlib import Path

LABELS = ["Fist", "One finger", "Two fingers", "Three fingers", "Four fingers", "Open palm"]


def evaluate_csv(path: str):
    try:
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
    except ImportError as exc:
        raise RuntimeError("Install scikit-learn to run evaluation") from exc
    with open(path, newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or not {"ground_truth", "prediction"}.issubset(rows[0]):
        raise ValueError("CSV requires ground_truth and prediction columns and at least one sample")
    truth, pred = [r["ground_truth"].strip() for r in rows], [r["prediction"].strip() for r in rows]
    p, r, f, support = precision_recall_fscore_support(truth, pred, labels=LABELS, zero_division=0)
    matrix = confusion_matrix(truth, pred, labels=LABELS)
    return {"accuracy": accuracy_score(truth, pred), "per_gesture": {
        label: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(support[i])}
        for i, label in enumerate(LABELS)}, "confusion_matrix": matrix.tolist(), "labels": LABELS, "samples": len(rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="CSV with ground_truth,prediction columns")
    parser.add_argument("--report", help="Write JSON evaluation report")
    args = parser.parse_args()
    import json
    report = evaluate_csv(args.csv)
    output = json.dumps(report, indent=2)
    print(output)
    if args.report:
        Path(args.report).write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
