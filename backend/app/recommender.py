"""
Recommender core — v2.

Combines (1) a trained 7-way mental-health category classifier, (2) a
separately-tuned, high-recall escalation trigger, (3) age band, and
(4) AU-specific seasonal signal into a ranked list of therapies plus a
triage decision. See ml/DESIGN.md for the modeling rationale and
ml/ESCALATION_LADDER.md for how the escalation flag is meant to be used
downstream.

This replaces the v1 DistilBERT-binary-sentiment approach. Two real,
trained models (trained via ml/02_*.py and ml/03_*.py on a public
mental-health text dataset) are loaded from ml/artifacts/ at startup. If
those artifacts don't exist yet (e.g. fresh clone, models not trained),
this module fails loudly when a classifier function is first called
rather than silently falling back to something fake — a missing-model
state should never be invisible.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import joblib
from scipy.sparse import hstack

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml"))
from features import ENGINEERED_FEATURE_COLS, engineer_features  # noqa: E402

THERAPIES = ["audio", "yoga", "reading", "laughing", "spirituality"]

AU_TZ = ZoneInfo("Australia/Sydney")

AU_SEASON_BY_MONTH = {
    12: "summer", 1: "summer", 2: "summer",
    3: "autumn", 4: "autumn", 5: "autumn",
    6: "winter", 7: "winter", 8: "winter",
    9: "spring", 10: "spring", 11: "spring",
}

# Internal IDs (audio/yoga/reading/laughing/spirituality) stay as stable
# keys — they're used in scoring, in the database's top_recommendation
# column, and changing them would mean a data migration for no benefit.
# Only the user-facing label and target page change to need-state framing.
# See frontend IA notes: each "page" below is now a blended need-state
# page containing 2-3 tools, not a single named therapy.
THERAPY_LABELS = {
    "audio": "Something to help you switch off",
    "yoga": "A moment to move and breathe",
    "reading": "A different way to look at it",
    "laughing": "Something to lighten the mood",
    "spirituality": "A bit of quiet and stillness",
}

THERAPY_PAGES = {
    "audio": "switch-off.html",
    "yoga": "move-and-breathe.html",
    "reading": "different-perspective.html",
    "laughing": "lighten-up.html",
    "spirituality": "stillness.html",
}

ML_ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts")

# Category -> set of weighted therapy nudges. NOT a severity ordering (see
# ml/DESIGN.md) — these are content-matching nudges, not clinical claims.
# "Normal" intentionally gets a light, non-urgent nudge; every clinical
# category gets nudges toward therapies the literature-informed framing in
# DESIGN.md associates with that kind of concern (e.g. grounding/low-effort
# content for anxiety/depression-coded text, rather than something that
# demands sustained focus).
CATEGORY_THERAPY_WEIGHTS = {
    "Normal": {"audio": 1.0, "yoga": 1.0},
    "Anxiety": {"audio": 2.0, "yoga": 1.5, "reading": -0.5},
    "Depression": {"audio": 1.5, "laughing": 1.0, "spirituality": 1.0, "reading": -1.0},
    "Stress": {"yoga": 2.0, "audio": 1.5},
    "Bipolar": {"yoga": 1.5, "spirituality": 1.0},
    "Personality disorder": {"spirituality": 1.5, "audio": 1.0},
    "Suicidal": {"audio": 1.0},  # de-prioritized: escalation flag is the real response here
}


@dataclass
class RecommendationResult:
    category: str
    category_confidence: float
    escalation_flag: bool
    escalation_probability: float
    season: str
    ranked: list[dict]


@lru_cache(maxsize=1)
def _load_category_classifier():
    path = os.path.join(ML_ARTIFACT_DIR, "category_classifier.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Train it first: "
            "cd backend && pip install -r ml/requirements-ml.txt && "
            "python ml/01_explore_data.py && python ml/02_train_category_classifier.py"
        )
    return joblib.load(path)


@lru_cache(maxsize=1)
def _load_escalation_trigger():
    path = os.path.join(ML_ARTIFACT_DIR, "escalation_trigger.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Train it first: "
            "python ml/03_train_escalation_trigger.py (after 01 and 02)"
        )
    return joblib.load(path)


def _featurize(text: str, vectorizer, scaler):
    import pandas as pd

    df = pd.DataFrame({"text": [text]})
    df_feat = engineer_features(df, text_col="text")
    tfidf = vectorizer.transform(df_feat["text"])
    engineered = scaler.transform(df_feat[ENGINEERED_FEATURE_COLS])
    return hstack([tfidf, engineered]).tocsr()


def classify_category(text: str) -> tuple[str, float]:
    """Returns (predicted_category, confidence) from the trained 7-way
    classifier. Confidence is the model's predicted probability for the
    winning class."""
    bundle = _load_category_classifier()
    X = _featurize(text, bundle["vectorizer"], bundle["scaler"])
    model = bundle["model"]

    pred = model.predict(X)[0]
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = list(model.classes_)
        confidence = float(proba[classes.index(pred)])
    else:
        confidence = 1.0  # model has no probability output; treat as certain

    return pred, round(confidence, 4)


def check_escalation(text: str) -> tuple[bool, float]:
    """Returns (should_escalate, probability) from the dedicated,
    recall-floor-tuned binary trigger. Independent of classify_category —
    see ml/DESIGN.md for why this must not just be "is Suicidal the top
    category"."""
    bundle = _load_escalation_trigger()
    X = _featurize(text, bundle["vectorizer"], bundle["scaler"])
    proba = bundle["model"].predict_proba(X)[0, 1]
    flag = bool(proba >= bundle["threshold"])
    return flag, round(float(proba), 4)


def get_au_season(month: int | None = None) -> str:
    if month is None:
        month = datetime.now(AU_TZ).month
    return AU_SEASON_BY_MONTH[month]


def score_therapies(category: str, age: int, season: str) -> dict[str, float]:
    """Transparent scoring function. Each block is a named, justified rule."""
    scores = {t: 0.0 for t in THERAPIES}

    category_weights = CATEGORY_THERAPY_WEIGHTS.get(category, {})
    for therapy, weight in category_weights.items():
        scores[therapy] += weight

    # Age-band preference, carried over from the original product's logic
    # and kept explicit (see git history) rather than discarded.
    if age <= 25:
        scores["laughing"] += 1.5
    elif age <= 40:
        scores["reading"] += 1.0
    elif age <= 60:
        scores["yoga"] += 1.0
    else:
        scores["spirituality"] += 1.5

    # AU seasonal signal — heuristic, not a clinical claim (see DESIGN.md).
    if season == "winter":
        scores["audio"] += 0.5
        scores["yoga"] += 0.5
    elif season == "summer":
        scores["yoga"] += 0.5
        scores["spirituality"] += 0.3

    return scores


def recommend(age: int, text: str, month: int | None = None) -> RecommendationResult:
    category, cat_conf = classify_category(text)
    escalation_flag, escalation_proba = check_escalation(text)
    season = get_au_season(month)
    scores = score_therapies(category, age, season)

    ranked_keys = sorted(scores, key=scores.get, reverse=True)
    ranked = [
        {
            "id": k,
            "label": THERAPY_LABELS[k],
            "score": round(scores[k], 3),
            "page": THERAPY_PAGES[k],
        }
        for k in ranked_keys
    ]

    return RecommendationResult(
        category=category,
        category_confidence=cat_conf,
        escalation_flag=escalation_flag,
        escalation_probability=escalation_proba,
        season=season,
        ranked=ranked,
    )
