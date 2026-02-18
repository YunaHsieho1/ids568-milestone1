# Milestone 2: Containerization & CI/CD

ML inference service (Iris classifier) with multi-stage Docker image and GitHub Actions CI/CD.

[![Build and Push ML Service](https://github.com/YOUR_USERNAME/ids568-milestone1/actions/workflows/build.yml/badge.svg)](https://github.com/YOUR_USERNAME/ids568-milestone1/actions/workflows/build.yml)

## Quick start (local)

```bash
# From repo root: ensure model exists
cd module3/milestone2
# If model.pkl missing: from repo root run:
#   MODEL_PATH=module3/milestone2/app/model.pkl python train_model.py

# Run tests
pip install -r app/requirements.txt -r requirements-dev.txt
pytest tests/ -v

# Build and run with Docker
docker build -t ml-service:local .
docker run -p 8080:8080 ml-service:local

# Or with docker-compose
docker compose up --build
```

- API docs: http://localhost:8080/docs  
- Health: http://localhost:8080/health  
- Predict: `POST /predict` with JSON body `{ "sepal_length", "sepal_width", "petal_length", "petal_width" }`

## Pull and run the image (Google Artifact Registry)

After pushing with a version tag (e.g. `v1.0.0`):

```bash
# Configure Docker for Artifact Registry (one-time)
gcloud auth configure-docker us-central1-docker.pkg.dev

# Pull and run
docker pull us-central1-docker.pkg.dev/milestone1-tzuyu/docker/ml-service:v1.0.0
docker run -p 8080:8080 us-central1-docker.pkg.dev/milestone1-tzuyu/docker/ml-service:v1.0.0
```

## Semantic versioning & push to registry

**詳細設定步驟請看 [設定說明.md](./設定說明.md)**（從 GCP 建立倉庫、金鑰到 GitHub Secret 與 tag 推送）。

簡述：
1. Add GitHub Secret **`GCP_SA_KEY`**: value = full JSON key of service account `artifact-registry-push` (GCP Console → IAM → Service accounts → Keys → Add key → JSON).  
2. Ensure Artifact Registry has a Docker repo (e.g. name `docker`, region `us-central1`).  
3. Tag and push to trigger build and push:

```bash
git tag v1.0.0
git push origin v1.0.0
```

See [RUNBOOK.md](./RUNBOOK.md) for operations, optimization, and troubleshooting.
