"""
Step 1: load the dataset, check what we actually have before modeling it.

This is deliberately a separate, runnable-first script rather than folding
exploration into the training script. Class balance and label-quality
issues need to be seen and reported BEFORE choosing model/metric design —
not discovered after the fact and rationalized.

Run: python ml/01_explore_data.py
Requires: pip install datasets pandas (see requirements-ml.txt)
"""

import pandas as pd
from datasets import load_dataset

OUT_DIR = "ml/artifacts"


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Loading btwitssayan/sentiment-analysis-for-mental-health from Hugging Face Hub...")
    ds = load_dataset("btwitssayan/sentiment-analysis-for-mental-health")
    df = ds["train"].to_pandas()

    print(f"\nTotal rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # The HF mirror's exact column names vary slightly by version; handle
    # both common cases defensively rather than assuming.
    text_col = "statement" if "statement" in df.columns else df.columns[0]
    label_col = "status" if "status" in df.columns else df.columns[-1]
    print(f"Using text column: '{text_col}', label column: '{label_col}'")

    df = df.rename(columns={text_col: "text", label_col: "label"})
    df = df.dropna(subset=["text", "label"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0]

    print(f"\nRows after dropping empty/null: {len(df)}")

    print("\n--- Class balance (this determines our eval strategy) ---")
    counts = df["label"].value_counts()
    pct = (counts / len(df) * 100).round(1)
    for label, count in counts.items():
        print(f"  {label:25s} {count:6d}  ({pct[label]}%)")

    minority_classes = counts[counts < counts.median() * 0.3]
    if len(minority_classes) > 0:
        print(f"\nWARNING — minority classes detected (less than 30% of median class size):")
        for label, count in minority_classes.items():
            print(f"  {label}: {count} rows — stratified split and macro-F1 are essential here, not accuracy.")

    print("\n--- Text length distribution ---")
    df["text_len"] = df["text"].str.len()
    df["word_count"] = df["text"].str.split().str.len()
    print(df[["text_len", "word_count"]].describe().round(1))

    print("\n--- Sample rows per class (sanity check the labels look plausible) ---")
    for label in counts.index:
        sample = df[df["label"] == label]["text"].iloc[0]
        truncated = sample[:120] + ("..." if len(sample) > 120 else "")
        print(f"  [{label}] {truncated}")

    df.to_parquet(f"{OUT_DIR}/cleaned_data.parquet", index=False)
    print(f"\nSaved cleaned data to {OUT_DIR}/cleaned_data.parquet")
    print("Next: python ml/02_train_category_classifier.py")


if __name__ == "__main__":
    main()
