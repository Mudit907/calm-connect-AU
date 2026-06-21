# CalmConnect ML pipeline — design notes

This document exists because the modeling choices here matter more than the
code, and because a reviewer (recruiter, professor, interviewer) should be
able to read this and trust the reasoning without running anything.

## What the dataset actually is

Source: `btwitssayan/sentiment-analysis-for-mental-health` on Hugging Face
Hub (mirrors a Kaggle dataset by Suchintika Sarkar, "Sentiment Analysis for
Mental Health"). 52,681 short, user-generated text statements, each
labelled with one of seven classes: `Normal`, `Anxiety`, `Depression`,
`Suicidal`, `Stress`, `Bipolar`, `Personality disorder`.

**What the labels are not**: clinician-assigned diagnoses. They are
almost certainly derived from subreddit membership or similar
self-identification heuristics by the original dataset compiler — meaning
a label of "Depression" means "this text resembles what people who
self-identify with depression-related communities write," not "a clinician
confirmed this person has depression." This distinction is stated here
explicitly and should be repeated anywhere these results are presented.
Treating model output as anything resembling a diagnosis would be both
inaccurate and irresponsible.

## Why this is not an ordinal severity scale

It would be tempting to map the 7 classes onto a single 0-6 "severity"
axis and train a regressor or ordinal classifier. This is rejected here as
conceptually wrong: Bipolar disorder is not "more severe" than Anxiety,
and Personality disorder is not "between" Stress and Suicidal on some
single axis. These are different categories of concern, not gradations of
one thing. Forcing them onto an ordinal scale would manufacture a false
sense of precision and is exactly the kind of modeling error that
undermines credibility with anyone who knows the domain.

**What we model instead**: two separate, honestly-scoped tasks.

### Task 1 — Category classification (multi-class, 7-way)

A standard multi-class classifier predicting the most likely category
label. Used to inform *which kind of support framing* might be relevant
(e.g. anxiety-coded text → grounding/breathing-oriented framing;
depression-coded text → gentle-activation framing) — not to diagnose, and
the product copy must never claim otherwise.

Model: TF-IDF features + a regularized linear classifier (logistic
regression, one-vs-rest) as the primary model, with a gradient-boosted
tree (LightGBM) as a comparison model. Both are chosen for
interpretability over raw accuracy — feature/coefficient inspection is a
deliverable here, not an afterthought, because explaining *why* the model
said what it said is part of what makes this defensible.

### Task 2 — Escalation trigger (binary, conservative)

A separate, deliberately conservative binary classifier: does this text
warrant surfacing crisis resources, independent of which category "wins"
in Task 1? This is not simply "is `Suicidal` the argmax of Task 1" —
argmax can be wrong, and for a safety-relevant decision, optimizing for
overall accuracy is the wrong objective.

Design choices specific to this task:
- Trained as `Suicidal` vs. everything else (binary), so it gets its own
  threshold separate from the 7-way decision boundary.
- Threshold is chosen by maximizing **recall at a recall floor** (e.g.
  fix recall >= 0.9, see what precision that costs), not by maximizing
  F1 or accuracy. The stated, deliberate tradeoff: more false positives
  (occasionally showing crisis resources to someone who didn't need
  them — low cost, mildly unnecessary) is preferred over false negatives
  (failing to surface support to someone who needed it — high cost).
  This asymmetry is the actual design decision and should be described
  exactly this way in any presentation of this work.
- Reported with a full confusion matrix and the recall/precision
  trade-off curve, not just a single accuracy number, precisely because a
  single number hides the asymmetry that matters.

## Features

Beyond TF-IDF text features, the following are engineered and reported
with feature importance / coefficients:
- Text length, word count (very short or very long statements behave
  differently)
- Punctuation intensity (e.g. exclamation/question mark density) as a
  rough arousal proxy
- First-person pronoun rate (self-focus, a known correlate in this
  literature — see references below)
- Presence of explicit temporal language ("always," "never," "lately")
  as a rough rumination proxy

These are documented as heuristic, literature-informed features, not
claimed as validated clinical markers.

## Evaluation

- Stratified train/val/test split (the `Suicidal` and `Personality
  disorder` classes are almost certainly minority classes — this is
  checked and reported, not assumed).
- Task 1: macro-F1 (treats all 7 classes as equally important, appropriate
  since this is not an accuracy-at-all-costs problem), full confusion
  matrix, per-class precision/recall.
- Task 2: ROC curve, precision-recall curve, and the specific
  recall-floor threshold analysis described above. Calibration curve
  (reliability diagram) checked — a model whose "0.7 confidence" doesn't
  actually correspond to being right ~70% of the time is a real problem
  for any system that surfaces confidence-based messaging to a user.
- All metrics tracked in MLflow alongside Phase 1's existing recommender
  experiment, as a new experiment (`calmconnect-mental-health-classifier`)
  so the two are comparable and both reproducible.

## What this still doesn't do (stated honestly)

- No clinical validation. This is a defensible, well-evaluated ML
  artifact built on weakly-labelled public data — it is explicitly not a
  diagnostic tool and the product copy must reflect that.
- No demographic/fairness audit of the underlying dataset (who wrote
  these posts, what populations are over/under-represented). This is a
  real limitation worth naming if asked, and a legitimate "future work"
  item rather than something to quietly omit.
- Trained on English-language, primarily social-media-register text. May
  not generalize well to how people in other contexts (e.g. a
  conversational chat interface, or different English dialects/registers
  including Australian colloquialisms) actually phrase things. Worth
  testing explicitly against a small hand-written AU-English sample
  before trusting this in the live product (see `eval_au_samples.py`).

## References

- Cohan et al., SMHD dataset and related work on self-reported mental
  health conditions from social media — for the broader methodological
  context of label quality in this kind of data.
- Stepped-care models in mental health service design (e.g. UK NHS IAPT
  framework) — informs the escalation-ladder framing in Phase 3, where
  the recall-floor design choice above is the technical analogue of a
  "low threshold to escalate" clinical triage principle.
