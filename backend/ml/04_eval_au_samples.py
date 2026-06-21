"""
Step 4: a small, hand-written test set in Australian colloquial register,
used to sanity-check whether the trained models generalize beyond the
training data's primarily US-social-media-English register.

This is NOT a rigorous held-out test set — it's 30 hand-written examples,
intentionally small. Its job is to surface obvious failure modes (e.g. "I
am not coping, the council rates bill alone is doing my head in" being
misread, or AU slang for distress going unrecognized), not to produce a
publishable metric. Treat any result here as a qualitative flag for
further work, not a number to put on a CV.

Run: python ml/04_eval_au_samples.py
Requires: artifacts from 02 and 03 to already exist.
"""

import joblib
import pandas as pd
from scipy.sparse import hstack

from features import ENGINEERED_FEATURE_COLS, engineer_features

ARTIFACT_DIR = "ml/artifacts"

# Hand-written, AU-colloquial-register examples with a best-guess intended
# label. These are illustrative, not a validated annotation — written by
# the project author, not independently verified by a clinician.
AU_SAMPLES = [
    {"text": "Honestly mate I'm doing alright, just flat out with work but nothing major.", "expected": "Normal"},
    {"text": "I keep stuffing things up at work and I reckon everyone's noticed by now, can't shake the dread.", "expected": "Anxiety"},
    {"text": "Been flat as a tack for weeks, can't be bothered doing anything, not even seeing mates.", "expected": "Depression"},
    {"text": "Honestly don't see the point anymore, feels like everyone'd be better off without me around.", "expected": "Suicidal"},
    {"text": "Rent's gone up again and I'm stretched so thin I can't sleep, head's spinning all night.", "expected": "Stress"},
    {"text": "One week I'm on top of the world planning everything, next week I can't get out of bed, it's exhausting.", "expected": "Bipolar"},
    {"text": "Bit knackered today but had a good weekend up the coast, feeling pretty sorted.", "expected": "Normal"},
    {"text": "Can't switch off, heart's racing over nothing, keep catastrophising about uni results.", "expected": "Anxiety"},
    {"text": "Everything feels grey lately, even things I used to love doing feel like a chore.", "expected": "Depression"},
    {"text": "I've been thinking about ending it, can't see things getting better from here.", "expected": "Suicidal"},
    {"text": "Juggling three jobs and uni, absolutely cooked, no time to breathe.", "expected": "Stress"},
    {"text": "Good days I feel unstoppable, bad days I can barely function, it's all or nothing with me.", "expected": "Bipolar"},
]


def main():
    cat_bundle = joblib.load(f"{ARTIFACT_DIR}/category_classifier.joblib")
    esc_bundle = joblib.load(f"{ARTIFACT_DIR}/escalation_trigger.joblib")

    df = pd.DataFrame(AU_SAMPLES)
    df_feat = engineer_features(df, text_col="text")

    cat_tfidf = cat_bundle["vectorizer"].transform(df_feat["text"])
    cat_engineered = cat_bundle["scaler"].transform(df_feat[ENGINEERED_FEATURE_COLS])
    X_cat = hstack([cat_tfidf, cat_engineered]).tocsr()

    esc_tfidf = esc_bundle["vectorizer"].transform(df_feat["text"])
    esc_engineered = esc_bundle["scaler"].transform(df_feat[ENGINEERED_FEATURE_COLS])
    X_esc = hstack([esc_tfidf, esc_engineered]).tocsr()

    cat_preds = cat_bundle["model"].predict(X_cat)
    esc_proba = esc_bundle["model"].predict_proba(X_esc)[:, 1]
    esc_flag = (esc_proba >= esc_bundle["threshold"]).astype(int)

    correct = 0
    print(f"{'Expected':<20s} {'Predicted':<20s} {'Esc.Flag':<10s} {'Esc.Prob':<10s} Text")
    print("-" * 110)
    for i, row in df.iterrows():
        pred = cat_preds[i]
        is_match = pred == row["expected"]
        correct += is_match
        flag_str = "FLAGGED" if esc_flag[i] else "-"
        marker = "" if is_match else "  <-- mismatch"
        print(f"{row['expected']:<20s} {pred:<20s} {flag_str:<10s} {esc_proba[i]:.3f}     {row['text'][:50]}{marker}")

    print(f"\n{correct}/{len(df)} category predictions matched the author's expected label.")
    print(
        "\nThis is a qualitative check, not a metric — a low score here means "
        "'investigate which AU phrasings the model misreads,' not 'the model "
        "is bad.' Inspect the mismatches above and consider whether they're "
        "genuinely ambiguous text or a real register gap before concluding "
        "anything. Document whatever you find in DESIGN.md's limitations section."
    )


if __name__ == "__main__":
    main()
