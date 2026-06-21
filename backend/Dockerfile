# CalmConnect recommender API — production container image (v2)
#
# IMPORTANT: this image expects TRAINED MODEL ARTIFACTS to already exist
# at ml/artifacts/category_classifier.joblib and
# ml/artifacts/escalation_trigger.joblib before you build. Train them
# first (see ml/run_pipeline.sh) — this Dockerfile does NOT train models
# at build time, by design: training depends on pulling a public dataset
# from Hugging Face Hub, which is slow and non-reproducible to do on every
# build. Train once, ship the frozen artifact — standard practice.
#
# If the artifacts are missing, the build fails loudly at the COPY step
# below rather than silently shipping a container that 503s on every
# request.

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY ml/features.py ./ml/features.py

# Fails the build with a clear error if you forgot to train first —
# COPY of a missing path errors out rather than silently skipping.
COPY ml/artifacts/category_classifier.joblib ./ml/artifacts/category_classifier.joblib
COPY ml/artifacts/escalation_trigger.joblib ./ml/artifacts/escalation_trigger.joblib

EXPOSE 8000

# Render/Railway inject $PORT; default to 8000 for local runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
