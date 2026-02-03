# Milestone 1: Web & Serverless Model Serving

This repository contains the implementation for **Milestone 1** of the MLOps course.  
It serves a trained **scikit-learn** model using two deployment patterns:

1. A **FastAPI** web service deployed as a container on **Google Cloud Run**
2. A **Google Cloud Function** implementing the same inference logic

The purpose of this milestone is to compare lifecycle behavior, artifact handling, latency,
and reproducibility trade-offs between container-based and serverless model serving.

---

## Deployment URLs

| Component | Reference |
|---------|-----------|
| **Cloud Run Service** | https://milestone1-api-881527490614.us-central1.run.app |
| **Artifact Registry Image** | `us-central1-docker.pkg.dev/milestone1-tzuyu/ml-models/milestone1-api:latest` |
| **Cloud Function** | https://us-central1-milestone1-tzuyu.cloudfunctions.net/predict-iris |

### Inference Verification

**Cloud Run**
```bash
curl -X POST https://milestone1-api-881527490614.us-central1.run.app/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

**Cloud Function**
```bash
curl -X POST https://us-central1-milestone1-tzuyu.cloudfunctions.net/predict-iris \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

```

---

## Repository Structure

```
.
├── main.py              # FastAPI app with /predict endpoint
├── train_model.py       # Trains and serializes the model artifact
├── model.pkl            # Serialized scikit-learn model
├── requirements.txt     # Dependency specification (reproducible)
├── Dockerfile           # Container definition for Cloud Run
├── cloud_function/
│   ├── main.py          # Cloud Function inference handler
│   ├── requirements.txt
│   └── README.md
└── README.md

```

---

## Model and Lifecycle Overview

- **Model:** Random Forest classifier trained on the Iris dataset
- **Artifact:** Serialized as `model.pkl`
- **Lifecycle stage:** Deployment / Serving

Lifecycle flow:

Client → HTTP Request → Schema Validation → Model Artifact → Prediction → HTTP Response


---

## Setup (Reproducible)

### 1. Environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate   
pip install -r requirements.txt
```

> **macOS:** If `python` is not found, use `python3` instead (e.g. `python3 -m venv .venv`).

### 2. Train and save the model artifact

```bash
python3 train_model.py
```

This creates `model.pkl` in the project root (overridable with `MODEL_PATH`).

### 3. Run FastAPI locally

```bash
uvicorn main:app
```
> **Note:** Omit `--reload` to avoid infinite reloads (uvicorn watches `.venv` by default). Restart manually after code changes.

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  

---

## API Contract

### Endpoint
`POST /predict`

### Request
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

Response:

```json
{ "predicted_class": 0, "label": "setosa" }
```

The API accepts a JSON payload containing four numeric features and returns
the predicted class index along with its corresponding label.

Input validation is enforced using **Pydantic** in the FastAPI service and
explicit checks in the Cloud Function implementation.


---

## Cloud Run: Cold Start and Lifecycle

The FastAPI service is deployed to Google Cloud Run as a containerized application.

- **Cold start:** When the service scales from zero, the first request experiences
  additional latency due to container initialization and model loading.
- **Warm requests:** Subsequent requests reuse the same container and in-memory model.
- **Lifecycle:** Container startup → model loaded during application lifespan →
  ready to serve requests. Scaling to zero reduces cost but reintroduces cold starts.

---

## Serverless Function (Google Cloud Functions)

The same prediction logic is implemented as a Google Cloud Function to evaluate
a pure serverless deployment pattern.

### Deployment

```bash
cd cloud_function
cp ../model.pkl .
gcloud functions deploy predict-iris \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=predict \
  --trigger-http \
  --allow-unauthenticated
cd ..
```

### Invoke

```bash
curl -X POST https://us-central1-milestone1-tzuyu.cloudfunctions.net/predict-iris \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

---

## Comparative Analysis: Cloud Run (FastAPI) vs Cloud Function

| Aspect | Cloud Run (FastAPI) | Cloud Function |
|------|---------------------|----------------|
| **Execution model** | Long-lived container | Event-driven function |
| **State handling** | Stateful per container (model kept in memory for container lifetime) | Stateless per invocation; instance may cache model during warm invocations |
| **Artifact loading** | Loaded once at container startup via FastAPI lifespan | Loaded on cold start per instance; reused on warm invocations |
| **Cold start latency (observed)** | ~11.9 s | ~5.9–7.4 s |
| **Warm latency (observed)** | ~0.09–0.15 s | ~0.14 s |
| **Reproducibility** | High (Docker image with pinned dependencies and model artifact) | Moderate (function source with pinned dependencies and model artifact) |
| **Scaling behavior** | Scales to zero; scales by container | Scales to zero; scales per request |
| **Typical use case** | Multi-endpoint services with middleware and greater runtime control | Lightweight, single-purpose inference endpoints |

**Observed behavior:**  
Both deployments use the same model artifact and inference logic. Cold start latency
varies depending on platform state, region, and runtime conditions. In observed tests,
Cloud Run exhibited a longer cold start (~11.9 s), while Cloud Function cold starts
ranged from ~5.9 to 7.4 s. After warm-up, latency was comparable across both patterns
(~0.1–0.15 s), with Cloud Run often slightly faster due to container reuse and
in-memory model persistence.

**Summary:**  
Cloud Run (FastAPI) provides a stateful container environment with predictable warm
latency and greater control over the serving runtime. Cloud Functions offer a simpler,
more serverless deployment model with lower operational overhead, but typically incur
higher cold start costs and a per-invocation lifecycle.

---

## Evidence Checklist

- [x] **FastAPI (local):** `uvicorn main:app` runs successfully and `/predict` returns valid predictions.
- [x] **Cloud Run:** Service deployed with public HTTPS URL, Artifact Registry image reference, and verified inference via `curl`.
- [x] **Cloud Function:** Function deployed with public URL and verified inference via `curl`.
- [x] **Comparative analysis:** Cold and warm start latency measured and documented in the table above with observed results.

---

## Requirements & Constraints Met

- **Language:** Python
- **Framework:** FastAPI
- **Cloud:** Google Cloud (Cloud Run and Cloud Functions)
- **Model:** Scikit-learn (Random Forest on Iris dataset), saved as `model.pkl`
- **Registry:** GCP Artifact Registry for Cloud Run image.

---

## Notes

- **Model path:** Set `MODEL_PATH` if `model.pkl` is not in the working directory (e.g., in Docker or Cloud Run).
- **Credentials:** Use environment variables and GCP IAM; do not hardcode secrets.
- **Reproducibility:** Keep `requirements.txt` (and Cloud Function dependencies) pinned and document the exact image or function version used for submission.
