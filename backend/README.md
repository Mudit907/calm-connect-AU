# CalmConnect — Recommender API (v2)

A FastAPI service that recommends a therapy module (audio, yoga, reading,
laughter, spirituality) based on a short mood description, age, and the
current Australian season — backed by two trained models rather than
heuristics, plus a documented escalation/triage design grounded in
stepped-care literature.

**If you're reviewing this project**: start with `ml/DESIGN.md` (the
modeling reasoning) and `ml/ESCALATION_LADDER.md` (the triage design).
Those two documents are arguably more important than the code — they're
where the actual thinking lives.

## What changed from v1

v1 used a pretrained binary sentiment model (DistilBERT) widened into 5
buckets via a confidence heuristic, feeding a hand-written scoring
function. It was honest about being a v1, but the "ML" in the story was
thin — a pretrained off-the-shelf model and a rule-based ranker, evaluated
against synthetic ground truth the project itself invented.

v2 replaces this with:
- A **trained 7-way category classifier** (Anxiety / Depression / Normal /
  Suicidal / Stress / Bipolar / Personality disorder) trained on a real
  public mental-health text dataset, with engineered features, model
  comparison (logistic regression vs. LightGBM), macro-F1 evaluation, and
  a full confusion matrix — not assumed to be a severity scale (see
  `ml/DESIGN.md` for why that distinction matters).
- A **dedicated escalation trigger** — a separate binary classifier whose
  decision threshold is chosen by a recall floor, not by accuracy. This
  is the actual safety-relevant component, and it's documented as such.
- A **stepped-care-grounded escalation ladder** (`ml/ESCALATION_LADDER.md`)
  that gives the binary flag an actual product meaning, rather than just
  toggling a banner.

## Architecture

```
backend/
  app/
    main.py         FastAPI app: /health, /recommend, /crisis-resources
    recommender.py  Loads trained models, combines with AU-seasonal logic
    _deprecated_v1/ Superseded v1 eval code, kept for history (see its README)
  ml/
    DESIGN.md              Modeling rationale — read this first
    ESCALATION_LADDER.md   Triage/escalation design, grounded in stepped-care literature
    features.py             Shared feature engineering (used by training AND serving)
    01_explore_data.py      Data loading + class-balance / label-quality checks
    02_train_category_classifier.py   Task 1: 7-way category classifier
    03_train_escalation_trigger.py    Task 2: recall-floor-tuned binary trigger
    04_eval_au_samples.py   Qualitative AU-English generalization check
    run_pipeline.sh         Runs 01-04 in order
    artifacts/              Trained model files (gitignored — train locally)
  Dockerfile        Expects trained artifacts to exist before building
  requirements.txt  Serving dependencies only (training deps in ml/requirements-ml.txt)
```

## Setup

```bash
cd backend
pip install -r requirements.txt          # serving deps
pip install -r ml/requirements-ml.txt    # training deps (separate, heavier)

# Train both models (downloads a public HF dataset, ~50k rows)
bash ml/run_pipeline.sh

# Then run the API
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`.

**If you call `/recommend` before training**, you'll get a `503` with an
explicit message telling you to train first — this is intentional (see
`app/main.py`'s `_models_present()` check). A missing-model state should
never be invisible.

## On the dataset and what the labels mean

Source: `btwitssayan/sentiment-analysis-for-mental-health` on Hugging Face
Hub. **The labels are not clinician-assigned diagnoses** — they almost
certainly derive from subreddit membership or similar self-identification
signals in the original data compilation. This is stated explicitly in
`ml/DESIGN.md` and should be repeated in any presentation of this project.
The model predicts "what category of concern this text resembles," not
"what condition this person has."

## On real metrics

I (the assistant who built this pipeline) could not execute training here
— `huggingface.co` isn't reachable from the sandbox this was built in.
Every script was tested end-to-end against a small synthetic stand-in
dataset purely to verify the code runs correctly (correct shapes, correct
threshold logic, no crashes) — **not** to produce real numbers. Run
`bash ml/run_pipeline.sh` yourself to get real macro-F1, recall/precision,
and calibration results before presenting any numbers from this project.

A sanity check: if your results look suspiciously perfect (e.g. macro-F1
near 1.0), something is wrong — likely test-set leakage or an
overly-easy synthetic stand-in still lying around in `ml/artifacts/`.
Real social-media mental-health text is messy; expect meaningfully
imperfect numbers, and treat reporting them honestly (including the
false-negative count from the escalation trigger) as more impressive than
a suspiciously clean result.

## Deployment (Render free tier)

1. Train models locally first: `bash ml/run_pipeline.sh` (this populates
   `ml/artifacts/`, which is gitignored — you'll need to either commit the
   trained `.joblib` files for this specific deployment path, or adjust
   your CI/deploy process to train as a build step. The Dockerfile as
   written expects the artifacts to already exist in the build context).
2. Push to GitHub, including the trained `.joblib` files (consider Git
   LFS if they're large).
3. On Render: New → Web Service → connect repo → root directory `backend/`
   → environment: Docker.
4. Update `frontend/assets/api.js`'s `API_BASE_URL` once deployed.

## Known limitations (stated honestly)

- Labels are weak/self-report-derived, not clinically validated (see above).
- The escalation trigger is tuned for a 0.90 recall floor on whatever data
  it was trained/validated on — this number is not a guarantee on live
  traffic, and should be re-checked periodically against real
  `data/interaction_log.csv` data once volume exists.
- No demographic/fairness audit of the underlying dataset.
- Trained on primarily US-social-media-register English. `ml/04_eval_au_samples.py`
  is a small, non-rigorous qualitative check for AU-English generalization
  gaps — treat its output as a todo list, not a pass/fail gate.
- This is not a clinical tool, has no regulatory approval, and should
  never be presented as equivalent to professional mental health care.
  The escalation ladder design explicitly positions it as a bridge to —
  not a replacement for — real support (see `ml/ESCALATION_LADDER.md`).
