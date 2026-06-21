"""
Feature engineering shared by both the category classifier and the
escalation trigger. Kept as one module so both models see identically
computed features — avoids subtle train/serve skew between the two tasks.

Each engineered feature is heuristic and literature-informed, not a
validated clinical instrument — see ml/DESIGN.md.
"""

import re

import numpy as np
import pandas as pd

FIRST_PERSON_PRONOUNS = {"i", "me", "my", "mine", "myself"}
TEMPORAL_RUMINATION_WORDS = {"always", "never", "lately", "anymore", "constantly", "everyday", "every day"}


def _word_tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def engineer_features(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    """Adds engineered feature columns to df. Returns a new DataFrame
    (does not mutate the input) so callers can't accidentally double-apply."""
    out = df.copy()
    texts = out[text_col].astype(str)

    out["char_len"] = texts.str.len()
    out["word_count"] = texts.apply(lambda t: len(_word_tokens(t))).clip(lower=1)

    out["exclamation_rate"] = texts.str.count(r"!") / out["char_len"].clip(lower=1)
    out["question_rate"] = texts.str.count(r"\?") / out["char_len"].clip(lower=1)

    def first_person_rate(text: str) -> float:
        tokens = _word_tokens(text)
        if not tokens:
            return 0.0
        fp_count = sum(1 for t in tokens if t in FIRST_PERSON_PRONOUNS)
        return fp_count / len(tokens)

    out["first_person_rate"] = texts.apply(first_person_rate)

    def rumination_rate(text: str) -> float:
        tokens = _word_tokens(text)
        if not tokens:
            return 0.0
        rum_count = sum(1 for t in tokens if t in TEMPORAL_RUMINATION_WORDS)
        return rum_count / len(tokens)

    out["rumination_rate"] = texts.apply(rumination_rate)

    out["avg_word_len"] = out["char_len"] / out["word_count"]

    return out


ENGINEERED_FEATURE_COLS = [
    "char_len",
    "word_count",
    "exclamation_rate",
    "question_rate",
    "first_person_rate",
    "rumination_rate",
    "avg_word_len",
]
