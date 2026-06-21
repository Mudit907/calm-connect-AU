"""
Generates a synthetic offline-evaluation dataset for the CalmConnect recommender.

Why synthetic: there is no real user-interaction log yet (pre-launch project).
Synthetic ground truth lets us run a genuine offline eval (precision@k, MRR)
instead of just asserting the model "works" — every label here encodes a
defensible therapy-matching rule, documented inline, so the eval is auditable.

Ground truth rule (documented, not hidden in code):
  - Severe/moderate negative sentiment -> prioritise grounding, low-effort therapies
    (audio, breathing) over anything that requires sustained attention (reading).
  - Mild negative + younger age -> social/light therapies (laughing, audio) rank higher.
  - Mild negative + older age -> reflective therapies (spirituality, yoga) rank higher.
  - AU winter months (Jun-Aug) -> audio/yoga (indoor, low-light-dependent) get a
    documented seasonal boost; AU summer (Dec-Feb) -> outdoor-friendly framing
    (yoga, spirituality) gets a small boost. This mirrors the seasonal-affect
    literature (reduced daylight correlating with indoor-coping preference) without
    claiming clinical validity.

This file produces data/eval_set.csv used by eval.py.
"""

import csv
import random

random.seed(42)

THERAPIES = ["audio", "yoga", "reading", "laughing", "spirituality"]

AU_SEASON_BY_MONTH = {
    12: "summer", 1: "summer", 2: "summer",
    3: "autumn", 4: "autumn", 5: "autumn",
    6: "winter", 7: "winter", 8: "winter",
    9: "spring", 10: "spring", 11: "spring",
}

SENTIMENT_BUCKETS = [
    "Positive",
    "Neutral",
    "Negative - Mild",
    "Negative - Moderate",
    "Negative - Severe",
]


def ground_truth_ranking(age: int, sentiment: str, month: int) -> list[str]:
    """Documented rule-based ground truth used ONLY for offline eval labels.
    This is intentionally separate from the model being evaluated."""
    season = AU_SEASON_BY_MONTH[month]
    scores = {t: 0.0 for t in THERAPIES}

    if sentiment in ("Positive", "Neutral"):
        # No therapy strongly indicated; mild general preference only.
        scores["audio"] += 1
        scores["yoga"] += 1
        return sorted(scores, key=scores.get, reverse=True)

    severity = {
        "Negative - Mild": 1,
        "Negative - Moderate": 2,
        "Negative - Severe": 3,
    }[sentiment]

    # Grounding/low-effort therapies prioritised as severity increases.
    scores["audio"] += severity * 1.5
    scores["spirituality"] += severity * 1.0
    scores["reading"] -= severity * 0.5  # reading needs sustained attention

    if age <= 25:
        scores["laughing"] += 2.0
        scores["audio"] += 1.0
    elif age <= 40:
        scores["reading"] += 1.5
        scores["yoga"] += 1.0
    elif age <= 60:
        scores["yoga"] += 1.5
        scores["spirituality"] += 1.0
    else:
        scores["spirituality"] += 2.0
        scores["audio"] += 1.0

    if season == "winter":
        scores["audio"] += 0.5
        scores["yoga"] += 0.5
    elif season == "summer":
        scores["yoga"] += 0.5
        scores["spirituality"] += 0.3

    return sorted(scores, key=scores.get, reverse=True)


def random_text_for_sentiment(sentiment: str) -> str:
    bank = {
        "Positive": [
            "Feeling pretty good today, things are going well.",
            "Had a great walk this morning, in a good headspace.",
        ],
        "Neutral": [
            "Just an average day, nothing much happening.",
            "Feeling okay, a bit tired but fine overall.",
        ],
        "Negative - Mild": [
            "A bit stressed about work but managing.",
            "Feeling a little off today, not sure why.",
        ],
        "Negative - Moderate": [
            "Pretty anxious about everything going on right now.",
            "Struggling to focus, feeling quite low today.",
        ],
        "Negative - Severe": [
            "Everything feels overwhelming and I can't cope right now.",
            "I feel completely exhausted and hopeless about things.",
        ],
    }
    return random.choice(bank[sentiment])


def main(n_rows: int = 400):
    rows = []
    for _ in range(n_rows):
        age = random.randint(15, 75)
        sentiment = random.choice(SENTIMENT_BUCKETS)
        month = random.randint(1, 12)
        text = random_text_for_sentiment(sentiment)
        ranking = ground_truth_ranking(age, sentiment, month)
        rows.append({
            "age": age,
            "month": month,
            "text": text,
            "true_sentiment": sentiment,
            "gt_rank_1": ranking[0],
            "gt_rank_2": ranking[1],
            "gt_rank_3": ranking[2],
        })

    with open("data/eval_set.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to data/eval_set.csv")


if __name__ == "__main__":
    main()
