"""
Step 2: Task 1 — category classification (7-way: Normal / Anxiety /
Depression / Suicidal / Stress / Bipolar / Personality disorder).

Trains and compares two interpretable models (logistic regression,
LightGBM) on TF-IDF + engineered features. Reports macro-F1 (not plain
accuracy — see DESIGN.md for why), full confusion matrix, and per-class
precision/recall. Logs everything to MLflow.

Run: python ml/02_train_category_classifier.py
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
import seaborn as sns
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from features import ENGINEERED_FEATURE_COLS, engineer_features

ARTIFACT_DIR = "ml/artifacts"
RANDOM_STATE = 42


def load_data() -> pd.DataFrame:
    path = f"{ARTIFACT_DIR}/cleaned_data.parquet"
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run `python ml/01_explore_data.py` first."
        )
    return pd.read_parquet(path)


def build_features(df: pd.DataFrame, vectorizer: TfidfVectorizer, scaler: StandardScaler, fit: bool):
    """Combines TF-IDF sparse text features with scaled engineered features
    into one feature matrix. fit=True only on the training split."""
    df_feat = engineer_features(df, text_col="text")

    if fit:
        tfidf = vectorizer.fit_transform(df_feat["text"])
        engineered = scaler.fit_transform(df_feat[ENGINEERED_FEATURE_COLS])
    else:
        tfidf = vectorizer.transform(df_feat["text"])
        engineered = scaler.transform(df_feat[ENGINEERED_FEATURE_COLS])

    return hstack([tfidf, engineered]).tocsr()


def plot_confusion_matrix(cm, labels, path):
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=labels, yticklabels=labels, cmap="Blues")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Category classifier — confusion matrix (test set)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = load_data()

    print(f"Loaded {len(df)} rows. Class distribution:")
    print(df["label"].value_counts())

    # Stratified split is non-negotiable here given the minority classes
    # flagged in 01_explore_data.py — a random split risks near-zero
    # representation of e.g. 'Personality disorder' in test.
    train_df, test_df = train_test_split(
        df, test_size=0.2, stratify=df["label"], random_state=RANDOM_STATE
    )
    train_df, val_df = train_test_split(
        train_df, test_size=0.15, stratify=train_df["label"], random_state=RANDOM_STATE
    )

    print(f"\nSplit sizes — train: {len(train_df)}, val: {len(val_df)}, test: {len(test_df)}")

    vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=3, sublinear_tf=True)
    scaler = StandardScaler()

    X_train = build_features(train_df, vectorizer, scaler, fit=True)
    X_val = build_features(val_df, vectorizer, scaler, fit=False)
    X_test = build_features(test_df, vectorizer, scaler, fit=False)

    y_train, y_val, y_test = train_df["label"], val_df["label"], test_df["label"]
    labels_sorted = sorted(df["label"].unique())

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("calmconnect-mental-health-classifier")

    results = {}

    # --- Model A: Logistic Regression (primary — most interpretable) ---
    with mlflow.start_run(run_name="logreg-category-classifier"):
        clf = LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0)
        clf.fit(X_train, y_train)

        val_preds = clf.predict(X_val)
        test_preds = clf.predict(X_test)

        val_macro_f1 = f1_score(y_val, val_preds, average="macro")
        test_macro_f1 = f1_score(y_test, test_preds, average="macro")

        report = classification_report(y_test, test_preds, output_dict=True)
        cm = confusion_matrix(y_test, test_preds, labels=labels_sorted)

        cm_path = f"{ARTIFACT_DIR}/logreg_confusion_matrix.png"
        plot_confusion_matrix(cm, labels_sorted, cm_path)

        mlflow.log_param("model_type", "logistic_regression")
        mlflow.log_param("class_weight", "balanced")
        mlflow.log_param("tfidf_max_features", 8000)
        mlflow.log_metric("val_macro_f1", val_macro_f1)
        mlflow.log_metric("test_macro_f1", test_macro_f1)
        mlflow.log_artifact(cm_path)

        print(f"\n[Logistic Regression] val macro-F1: {val_macro_f1:.4f}, test macro-F1: {test_macro_f1:.4f}")
        print(classification_report(y_test, test_preds))

        results["logreg"] = {"model": clf, "test_macro_f1": test_macro_f1, "report": report}

    # --- Model B: LightGBM (comparison — usually stronger on tabular+text-stat blends) ---
    try:
        from lightgbm import LGBMClassifier

        with mlflow.start_run(run_name="lightgbm-category-classifier"):
            lgbm = LGBMClassifier(
                n_estimators=300, max_depth=8, class_weight="balanced", random_state=RANDOM_STATE, verbosity=-1
            )
            lgbm.fit(X_train, y_train)

            val_preds = lgbm.predict(X_val)
            test_preds = lgbm.predict(X_test)

            val_macro_f1 = f1_score(y_val, val_preds, average="macro")
            test_macro_f1 = f1_score(y_test, test_preds, average="macro")

            cm = confusion_matrix(y_test, test_preds, labels=labels_sorted)
            cm_path = f"{ARTIFACT_DIR}/lightgbm_confusion_matrix.png"
            plot_confusion_matrix(cm, labels_sorted, cm_path)

            mlflow.log_param("model_type", "lightgbm")
            mlflow.log_param("n_estimators", 300)
            mlflow.log_metric("val_macro_f1", val_macro_f1)
            mlflow.log_metric("test_macro_f1", test_macro_f1)
            mlflow.log_artifact(cm_path)

            print(f"\n[LightGBM] val macro-F1: {val_macro_f1:.4f}, test macro-F1: {test_macro_f1:.4f}")
            print(classification_report(y_test, test_preds))

            results["lightgbm"] = {"model": lgbm, "test_macro_f1": test_macro_f1}
    except ImportError:
        print("\nLightGBM not installed — skipping comparison model. `pip install lightgbm` to include it.")

    # --- Pick winner by macro-F1, save it + the featurizers together ---
    best_name = max(results, key=lambda k: results[k]["test_macro_f1"])
    print(f"\nBest model by test macro-F1: {best_name} ({results[best_name]['test_macro_f1']:.4f})")

    joblib.dump(
        {
            "model": results[best_name]["model"],
            "vectorizer": vectorizer,
            "scaler": scaler,
            "labels": labels_sorted,
            "model_type": best_name,
        },
        f"{ARTIFACT_DIR}/category_classifier.joblib",
    )
    print(f"Saved best model to {ARTIFACT_DIR}/category_classifier.joblib")

    with open(f"{ARTIFACT_DIR}/category_classifier_report.json", "w") as f:
        json.dump(
            {k: v for k, v in results[best_name].get("report", {}).items()},
            f,
            indent=2,
            default=str,
        )

    print("\nNext: python ml/03_train_escalation_trigger.py")


if __name__ == "__main__":
    main()
