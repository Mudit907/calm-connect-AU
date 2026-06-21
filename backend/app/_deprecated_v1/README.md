# Deprecated — v1 recommender evaluation

These two files (`eval.py`, `generate_eval_set.py`) evaluated the **v1**
recommender, which scored a DistilBERT binary-sentiment output against a
hand-rolled synthetic ground-truth set.

They are kept here, out of the active `app/` and `data/` paths, rather
than deleted outright — partly as a record of the project's evolution
(useful if you're asked "what changed and why" in an interview), and
partly because the recall-floor-vs-accuracy reasoning pattern they
contain is still conceptually relevant, just superseded by a more
rigorous version.

**They will not run as-is** — `app/recommender.py` no longer exposes the
`classify_sentiment` function they import.

**Replacement**: the v2 evaluation lives in `backend/ml/`:
- `ml/02_train_category_classifier.py` — trains + evaluates the category
  classifier (macro-F1, confusion matrix) against a real public dataset,
  not synthetic ground truth.
- `ml/03_train_escalation_trigger.py` — trains + evaluates the escalation
  trigger (recall-floor threshold selection, precision/recall, ROC-AUC,
  calibration), also against real data.
- `ml/04_eval_au_samples.py` — qualitative AU-English generalization
  check.

See `ml/DESIGN.md` for the full reasoning behind why v2 evaluates this
way instead of the synthetic-ground-truth approach used here in v1.
