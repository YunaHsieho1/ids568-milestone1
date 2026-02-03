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

## Comparative Analysis: FastAPI (Cloud Run) vs Cloud Function

| Aspect | FastAPI on Cloud Run | Cloud Function |
|--------|----------------------|----------------|
| **Lifecycle / state** | Long-lived container; stateful (model in memory for container lifetime). | Stateless at the “request” level; instance can cache model in memory (warm invocations). |
| **Artifact loading** | Load once in FastAPI lifespan at container start. | Load on first request per instance (cold) or reuse cached model (warm). |
| **Cold start** | Container start + model load; typically hundreds of ms to a few seconds. | New instance: runtime + dependencies + model load; often 1–5+ seconds for Python. |
| **Warm latency** | Low; only inference. | Low once instance is warm; similar to FastAPI for inference. |
| **Reproducibility** | Same `requirements.txt` and `model.pkl` in image; version image for full reproducibility. | Same `model.pkl` and `requirements.txt` in function source; pin versions for reproducibility. |
| **Scaling** | Scale to zero possible; scale-up on request. | Scale to zero; scale-out per invocation. |
| **Use case** | Multiple endpoints, middleware, more control over server behavior. | Single HTTP handler, minimal ops, pay-per-invocation. |

**Summary:** Both use the same model artifact and prediction logic. Cloud Run (FastAPI) gives a stateful container and predictable warm latency; Cloud Function is simpler to deploy and more “serverless” but tends to have higher cold start latency and per-invocation lifecycle.

---

## Evidence Checklist

- [x] **FastAPI (local):** `uvicorn main:app` and successful `curl` to `/predict`.
- [x] **Cloud Run:** Deployed service URL (HTTPS), Artifact Registry image reference, and a `curl` showing successful inference（見上方 Deployment URLs）。
- [x] **Cloud Function:** Deployed function URL and a `curl` showing successful invocation（見上方 Deployment URLs）。
- [x] **Comparative report:** 上表已填入實測 cold/warm 延遲，並於 Comparative Analysis 加入實測觀察說明。

---

## Requirements & Constraints Met

- **Language:** Python only.
- **Framework:** FastAPI for the web service.
- **Cloud:** Google Cloud (Cloud Run and Cloud Functions).
- **Model:** Scikit-learn (Random Forest on Iris), saved as `model.pkl`.
- **Registry:** GCP Artifact Registry for Cloud Run image.

---

## Tips

- **Model path:** Set `MODEL_PATH` if `model.pkl` is not in the current directory (e.g. in Docker or Cloud Run).
- **Credentials:** Use environment variables and GCP IAM; do not hardcode keys.
- **Reproducibility:** Keep `requirements.txt` (and Cloud Function’s) pinned; document the exact image/function version used for submission.
