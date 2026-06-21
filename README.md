# CalmConnect

A mood-aware wellbeing companion, built for people who can't easily access
or afford therapy, and who may not trust black-box AI mental-health tools.
A short, free-text description of how you're feeling plus your age is run
through a trained classifier and a separately-tuned, conservative
escalation trigger, then combined with AU-context-aware logic to surface
the most relevant of five self-help therapy modules — with a documented,
literature-grounded design for when self-help isn't enough.

**Live demo:** [calmconnect-au](https://mudit907.github.io/calm-connect-AU/) (frontend) · [API docs](https://calm-connect-au.onrender.com/docs) (backend, FastAPI auto-generated)

## Why this exists, and what changed

Originally a static site with a hardcoded if/else recommender. First
rebuilt into a deployed FastAPI service with a pretrained sentiment model.
That version was honest but thin — a pretrained off-the-shelf classifier
feeding a hand-written scoring function isn't really "the ML story" worth
telling.

This version (v2) replaces that with two **trained** models on a real
public mental-health text dataset, an escalation trigger designed around
a stated recall-vs-precision tradeoff rather than raw accuracy, and a
triage/escalation design explicitly grounded in stepped-care literature
(the framework real mental health services use to match care intensity to
need). See `backend/ml/DESIGN.md` and `backend/ml/ESCALATION_LADDER.md`
for the actual reasoning — they're the most important documents in this
repo, more so than the code.

## Structure

```
frontend/   Static site (HTML/CSS/JS), calls the backend API
backend/    FastAPI service + ml/ training pipeline
  backend/ml/DESIGN.md             Read this first
  backend/ml/ESCALATION_LADDER.md  Then this
```

## Stack

- **Frontend**: vanilla HTML/CSS/JS, no build step
- **Backend**: FastAPI, scikit-learn / LightGBM (trained models, not a
  pretrained black box), MLflow for experiment tracking, Docker for
  deployment
- **Modeling**: TF-IDF + engineered linguistic features → logistic
  regression / LightGBM, trained on `btwitssayan/sentiment-analysis-for-mental-health`
  (Hugging Face Hub)
- **Hosting**: Render free tier (backend), static hosting of choice
  (frontend)

## Running it locally

```bash
# Backend — train first, then serve
cd backend
pip install -r requirements.txt
pip install -r ml/requirements-ml.txt
bash ml/run_pipeline.sh
uvicorn app.main:app --reload

# Frontend — any static file server
cd frontend
python -m http.server 5500
```

Update `frontend/assets/api.js`'s `API_BASE_URL` to point at your backend
while developing.

## What this is, intellectually

This project is built around three real ideas, each documented rather
than just implemented:

1. **Category, not severity.** The seven mental-health categories in the
   training data are not an ordinal scale — modeling them as one would be
   a real conceptual error. `ml/DESIGN.md` explains why they're treated
   as separate concerns instead, and why escalation gets its own
   dedicated, separately-tuned model rather than reusing the category
   classifier's top prediction.
2. **Recall-floor design for the escalation trigger**, not accuracy
   optimization — a stated, deliberate tradeoff (more false positives
   are an acceptable cost for fewer false negatives in a safety-relevant
   decision), with the actual cost (false negative count) reported
   honestly rather than hidden behind a single aggregate metric.
3. **Stepped care as the product's organizing principle** — the
   escalation flag isn't just a UI toggle, it's mapped onto a real
   triage framework used in actual mental health service design, with
   the product's self-help modules explicitly framed as the
   least-intensive first step, not a replacement for anything above it.

## What's deliberately not built yet

- **Trajectory/longitudinal modeling** (detecting decline vs. a single
  bad day vs. recovery across repeated check-ins) is specified in
  `ml/ESCALATION_LADDER.md` as Steps 1-2 of the escalation ladder, but not
  implemented — it requires real multi-session interaction data that
  doesn't exist yet pre-launch. Building it on fabricated data would mean
  faking the exact kind of validation this project is trying to take
  seriously, so it's documented as a clear next step instead.
- See `backend/README.md`'s "Known limitations" section for the rest,
  including dataset label-quality caveats and AU-English generalization
  gaps — documented honestly because that's more credible than pretending
  v2 is more finished than it is.
