#!/usr/bin/env bash
# Runs the full ML pipeline in order. Run from backend/ directory.
# Requires: pip install -r ml/requirements-ml.txt

set -e

echo "=== Step 1: explore + clean data ==="
python ml/01_explore_data.py

echo ""
echo "=== Step 2: train category classifier (7-way) ==="
python ml/02_train_category_classifier.py

echo ""
echo "=== Step 3: train escalation trigger (binary, recall-floor) ==="
python ml/03_train_escalation_trigger.py

echo ""
echo "=== Step 4: qualitative AU-English generalization check ==="
python ml/04_eval_au_samples.py

echo ""
echo "=== Done. View experiment tracking with: mlflow ui --backend-store-uri sqlite:///mlflow.db ==="
