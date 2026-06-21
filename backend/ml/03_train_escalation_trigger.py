"""
Step 3: Task 2 — the escalation trigger. A separate, deliberately
conservative binary classifier: Suicidal vs. everything else, with the
decision threshold chosen by a RECALL FLOOR, not by maximizing accuracy
or F1. See ml/DESIGN.md for why this asymmetry is the actual design
decision here, not an implementation detail.

This script also checks calibration (does a predicted probability of 0.7
actually correspond to being right ~70% of the time?) — necessary before
this model's confidence score is ever shown to a user or used to drive
any UI behaviour.

Run: python ml/03_train_escalation_trigger.py
Requires: pip install -r ml/requirements-ml.txt
"""

import json
import os

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.calibration import calibration_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from features import ENGINEERED_FEATURE_COLS, engineer_features

ARTIFACT_DIR = "ml/artifacts"
RANDOM_STATE = 42
RECALL_FLOOR = 0.90  # the actual design decision: see DESIGN.md


def load_data() -> pd.DataFrame:
    path = f"{ARTIFACT_DIR}/cleaned_data.parquet"
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run `python ml/01_explore_data.py` first."
        )
    return pd.read_parquet(path)


def build_features(df, vectorizer, scaler, fit: bool):
    df_feat = engineer_features(df, text_col="text")
    if fit:
        tfidf = vectorizer.fit_transform(df_feat["text"])
        engineered = scaler.fit_transform(df_feat[ENGINEERED_FEATURE_COLS])
    else:
        tfidf = vectorizer.transform(df_feat["text"])
        engineered = scaler.transform(df_feat[ENGINEERED_FEATURE_COLS])
    return hstack([tfidf, engineered]).tocsr()


def choose_threshold_at_recall_floor(y_true, y_proba, recall_floor: float) -> tuple[float, float, float]:
    """Returns (threshold, precision_at_threshold, recall_at_threshold).

    Walks thresholds from high to low; picks the highest threshold that
    still clears the recall floor. Highest threshold at the floor =
    best precision we can get without sacrificing the recall guarantee.
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    # precision_recall_curve returns thresholds of length n-1 vs precisions/recalls of length n
    # align them by dropping the last precision/recall point
    precisions, recalls = precisions[:-1], recalls[:-1]

    valid = recalls >= recall_floor
    if not valid.any():
        # Cannot hit the floor at all — fall back to the threshold that
        # maximizes recall, and flag this loudly rather than silently
        # returning a useless threshold.
        best_idx = np.argmax(recalls)
        print(
            f"WARNING: no threshold achieves recall >= {recall_floor}. "
            f"Best achievable recall is {recalls[best_idx]:.3f}. "
            "This means the model itself isn't strong enough for this "
            "recall floor — revisit features/model before trusting this trigger."
        )
        return thresholds[best_idx], precisions[best_idx], recalls[best_idx]

    # Among thresholds clearing the floor, pick the one with best precision
    best_idx = np.argmax(np.where(valid, precisions, -1))
    return thresholds[best_idx], precisions[best_idx], recalls[best_idx]


def plot_pr_curve(y_true, y_proba, chosen_threshold, path):
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    plt.figure(figsize=(7, 5))
    plt.plot(recalls, precisions, label="Precision-Recall curve")
    plt.axvline(RECALL_FLOOR, color="grey", linestyle="--", label=f"Recall floor ({RECALL_FLOOR})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Escalation trigger — precision/recall trade-off")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_calibration(y_true, y_proba, path):
    frac_pos, mean_pred = calibration_curve(y_true, y_proba, n_bins=10)
    plt.figure(figsize=(6, 6))
    plt.plot(mean_pred, frac_pos, marker="o", label="Model")
    plt.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Perfectly calibrated")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title("Escalation trigger — calibration curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = load_data()

    # Binary reframing: Suicidal vs. everything else. This is intentionally
    # NOT "highest class wins" from Task 1 — it's a dedicated binary task
    # so it gets its own threshold, tuned for recall, independent of
    # Task 1's multi-class decision boundary. See DESIGN.md.
    df["is_high_risk"] = (df["label"] == "Suicidal").astype(int)
    print(f"High-risk class prevalence: {df['is_high_risk'].mean():.4f} ({df['is_high_risk'].sum()} / {len(df)})")

    train_df, test_df = train_test_split(
        df, test_size=0.2, stratify=df["is_high_risk"], random_state=RANDOM_STATE
    )
    train_df, val_df = train_test_split(
        train_df, test_size=0.15, stratify=train_df["is_high_risk"], random_state=RANDOM_STATE
    )

    vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=3, sublinear_tf=True)
    scaler = StandardScaler()

    X_train = build_features(train_df, vectorizer, scaler, fit=True)
    X_val = build_features(val_df, vectorizer, scaler, fit=False)
    X_test = build_features(test_df, vectorizer, scaler, fit=False)

    y_train, y_val, y_test = train_df["is_high_risk"], val_df["is_high_risk"], test_df["is_high_risk"]

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("calmconnect-mental-health-classifier")

    with mlflow.start_run(run_name="escalation-trigger-logreg"):
        clf = LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0)
        clf.fit(X_train, y_train)

        val_proba = clf.predict_proba(X_val)[:, 1]
        test_proba = clf.predict_proba(X_test)[:, 1]

        # Threshold chosen on VALIDATION set, evaluated on TEST set —
        # standard practice to avoid threshold-tuning leaking test info.
        threshold, val_precision, val_recall = choose_threshold_at_recall_floor(y_val, val_proba, RECALL_FLOOR)
        print(f"\nChosen threshold (from validation set): {threshold:.4f}")
        print(f"  Validation precision at this threshold: {val_precision:.4f}")
        print(f"  Validation recall at this threshold: {val_recall:.4f}")

        test_preds = (test_proba >= threshold).astype(int)
        test_cm = confusion_matrix(y_test, test_preds)
        tn, fp, fn, tp = test_cm.ravel()
        test_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        test_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        test_auc = roc_auc_score(y_test, test_proba)

        print(f"\nTest set at chosen threshold:")
        print(f"  Recall:    {test_recall:.4f}  (of all truly high-risk texts, what fraction did we flag?)")
        print(f"  Precision: {test_precision:.4f}  (of everything we flagged, what fraction was truly high-risk?)")
        print(f"  ROC-AUC:   {test_auc:.4f}")
        print(f"  Confusion matrix — TN: {tn}, FP: {fp}, FN: {fn}, TP: {tp}")
        if fn > 0:
            print(
                f"  WARNING: {fn} high-risk texts were NOT flagged at this threshold. "
                "This number should be reported honestly in any presentation of this work — "
                "it is the real cost of the precision we gained, and it is never zero."
            )

        pr_path = f"{ARTIFACT_DIR}/escalation_pr_curve.png"
        cal_path = f"{ARTIFACT_DIR}/escalation_calibration.png"
        plot_pr_curve(y_test, test_proba, threshold, pr_path)
        plot_calibration(y_test, test_proba, cal_path)

        mlflow.log_param("recall_floor", RECALL_FLOOR)
        mlflow.log_param("chosen_threshold", threshold)
        mlflow.log_metric("test_recall", test_recall)
        mlflow.log_metric("test_precision", test_precision)
        mlflow.log_metric("test_roc_auc", test_auc)
        mlflow.log_metric("test_false_negatives", int(fn))
        mlflow.log_metric("test_false_positives", int(fp))
        mlflow.log_artifact(pr_path)
        mlflow.log_artifact(cal_path)

        joblib.dump(
            {
                "model": clf,
                "vectorizer": vectorizer,
                "scaler": scaler,
                "threshold": threshold,
                "recall_floor_target": RECALL_FLOOR,
            },
            f"{ARTIFACT_DIR}/escalation_trigger.joblib",
        )
        print(f"\nSaved escalation trigger to {ARTIFACT_DIR}/escalation_trigger.joblib")

    print("\nNext: python ml/04_eval_au_samples.py")


if __name__ == "__main__":
    main()
