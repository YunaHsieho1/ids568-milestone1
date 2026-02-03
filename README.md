# Milestone 1: Web & Serverless Model Serving

MLOps Course - Module 2. This repository implements a complete model serving solution: a **FastAPI** microservice (local + **Cloud Run**) and a **Google Cloud Function** with the same inference logic, plus documentation of lifecycle and deployment-pattern trade-offs.

---

## Deployment URLs (本專案實際部署)

| 項目 | URL / 參考 |
|------|-------------|
| **Cloud Run 服務** | https://milestone1-api-881527490614.us-central1.run.app |
| **Artifact Registry 映像** | `us-central1-docker.pkg.dev/milestone1-tzuyu/ml-models/milestone1-api:latest` |
| **Cloud Function** | https://us-central1-milestone1-tzuyu.cloudfunctions.net/predict-iris |

**HTTPS 推論證據（Cloud Run）：**
```bash
$ curl -X POST https://milestone1-api-881527490614.us-central1.run.app/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
{"predicted_class":0,"label":"setosa"}
```

**HTTPS 推論證據（Cloud Function）：**
```bash
$ curl -X POST https://us-central1-milestone1-tzuyu.cloudfunctions.net/predict-iris \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
{"label":"setosa","predicted_class":0}
```

---

## Repository Structure

```
.
├── main.py              # FastAPI app: /predict, Pydantic schemas
├── train_model.py       # Train and save model.pkl (run once)
├── model.pkl            # Scikit-learn artifact (generate with train_model.py)
├── requirements.txt     # Reproducible environment
├── Dockerfile           # Container for Cloud Run
├── cloud_function/      # GCP Cloud Function (same prediction logic)
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
└── README.md            # This file
```

---

## Lifecycle: Input → Model → API → Consumer

1. **Input** – HTTP request with JSON body (4 features).
2. **Schema validation** – Pydantic (FastAPI) or manual checks (Cloud Function) ensure valid inputs.
3. **Model (artifact)** – `model.pkl` is loaded once at startup (FastAPI/Cloud Run) or per instance (Cloud Function); inference is deterministic.
4. **API** – `/predict` returns predicted class and label.
5. **Consumer** – Client receives structured response (e.g. `predicted_class`, `label`).

Model–API interaction: the API is a thin layer around the artifact; the same artifact and feature contract are used in both FastAPI and Cloud Function deployments.

---

## Setup (Reproducible)

### 1. Create virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
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

## API Usage

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Prediction (local or Cloud Run URL)

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'
```

Example response:

```json
{ "predicted_class": 0, "label": "setosa" }
```

Schema:

- **Request:** `sepal_length`, `sepal_width`, `petal_length`, `petal_width` (float, 0–10).
- **Response:** `predicted_class` (int: 0=setosa, 1=versicolor, 2=virginica), `label` (string).

---

## Cloud Run Deployment

### Prerequisites

- Google Cloud project with billing enabled.
- `gcloud` CLI installed and authenticated.
- Docker (optional; can use Cloud Build).

### Build and push to Artifact Registry

```bash
# Create repository (once)
gcloud artifacts repositories create ml-models --repository-format=docker --location=REGION

# Build and push (本專案：PROJECT_ID=milestone1-tzuyu, REGION=us-central1)
gcloud builds submit --tag us-central1-docker.pkg.dev/milestone1-tzuyu/ml-models/milestone1-api:latest .
```

### Deploy to Cloud Run

```bash
gcloud run deploy milestone1-api \
  --image us-central1-docker.pkg.dev/milestone1-tzuyu/ml-models/milestone1-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

After deployment you get an HTTPS URL. Test inference with:

```bash
curl -X POST https://milestone1-api-881527490614.us-central1.run.app/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
```

### Cold start and lifecycle (Cloud Run)

- **Cold start:** First request after idle may take longer (container start + model load).
- **Warm:** Subsequent requests reuse the same container and in-memory model.
- **Lifecycle:** Container starts → `load_model()` in lifespan → ready to serve; scaling to zero when idle reduces cost but reintroduces cold starts.

---

## Serverless Function (GCP Cloud Function)

Same prediction logic as the FastAPI service; different deployment and lifecycle.

### Deploy

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
| **Cold start** | Container start + model load; 實測約 **11.9 s**（冷啟動時）。 | New instance: runtime + dependencies + model load; 實測約 **5.9–7.4 s**（冷啟動時）。 |
| **Warm latency** | 實測約 **0.09–0.15 s**；僅推論。 | 實測約 **0.14 s**；warm 時與 FastAPI 相近。 |
| **Reproducibility** | Same `requirements.txt` and `model.pkl` in image; version image for full reproducibility. | Same `model.pkl` and `requirements.txt` in function source; pin versions for reproducibility. |
| **Scaling** | Scale to zero possible; scale-up on request. | Scale to zero; scale-out per invocation. |
| **Use case** | Multiple endpoints, middleware, more control over server behavior. | Single HTTP handler, minimal ops, pay-per-invocation. |

**實測觀察（本專案）：** 冷啟動時兩者延遲皆為數秒，單次實測 Cloud Run 曾達 ~11.9 s、Cloud Function ~5.9–7.4 s，會隨當時負載與區域而變。暖機後兩者皆約 0.1–0.15 s，差異不大；FastAPI (Cloud Run) 在 warm 時常略快。結論：兩者使用相同模型與推論邏輯，Cold start 時延遲較高且誰快誰慢不固定，Warm 時延遲相近、FastAPI 略快或相當。

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
