# Milestone 2 – Operations Runbook

## 1. Dependency pinning strategy (reproducibility)

- **Where**: `app/requirements.txt` (and `requirements-dev.txt` for tests).
- **How**: All dependencies use exact versions (e.g. `fastapi==0.109.2`). No ranges like `>=0.109`.
- **Why**: Same versions everywhere (local, CI, production) so builds and behavior are reproducible.
- **Update**: Change version numbers explicitly and re-run tests and build.

## 2. Image optimization

- **Technique**: Multi-stage Dockerfile:
  - **Builder stage**: Install Python deps with `pip install --user --no-cache-dir`; no app code in this stage.
  - **Runtime stage**: Copy only `/root/.local` from builder + app code and model; no build tools.
- **Layer order**: Dependencies (requirements.txt) first, then app code and model, so code changes don’t invalidate dependency cache.
- **Base**: `python:3.11-slim` for smaller size than full Python image.
- **Size check**: Run `docker build -t ml-service:test .` then `docker images ml-service:test` to record size. Compare after changes (e.g. switching to Alpine) if doing the optional comparison.

## 3. Security considerations

- **Minimal surface**: Runtime image has no compiler or dev packages; only what’s needed to run the app.
- **No secrets in repo**: Registry credentials go in GitHub Secrets; workflow uses a **Google service account key** stored as `GCP_SA_KEY`. No hardcoded passwords.

## 3b. Google Artifact Registry setup

- **Registry**: Google Artifact Registry (GAR). Image URL: `us-central1-docker.pkg.dev/milestone1-tzuyu/docker/ml-service:TAG`.
- **Service account**: `artifact-registry-push@milestone1-tzuyu.iam.gserviceaccount.com`. Ensure it has **Artifact Registry Writer** (or equivalent) on the repository.
- **GitHub Secret**: In repo → Settings → Secrets and variables → Actions, add secret **`GCP_SA_KEY`** with the **entire JSON key file** of the service account (create key in GCP Console → Service account → Keys → Add key → JSON).
- **Create repository if needed**: In GCP Console → Artifact Registry → Create repository → format **Docker**, name e.g. **`docker`**, region e.g. **`us-central1`**. If your repo name/region differ, set `GAR_REPOSITORY` and `GAR_REGION` in `.github/workflows/build.yml`.
- **Vulnerability scanning**: Optional (Challenge): add Trivy or Snyk step in `.github/workflows/build.yml` and fix critical findings.

## 4. CI/CD workflow (step-by-step)

1. **Trigger**: Push to `main`, push of tag `v*.*.*`, or pull request to `main`.
2. **Test job**:
   - Checkout repo → Set up Python 3.11 → Install `app/requirements.txt` and `requirements-dev.txt` → Run `pytest tests/` from `module3/milestone2`.
   - If tests fail, workflow fails; no build/push.
3. **Build job** (only on push to `main` or push of version tag):
   - After test passes: checkout → (if version tag) Authenticate to GCP with `GCP_SA_KEY` → Configure Docker for Artifact Registry → Docker Buildx → build image.
   - Tag: for version tags use the tag (e.g. `v1.0.0`); for branch push use `sha-<short-sha>`.
   - **Push only when the ref is a version tag** (e.g. `git tag v1.0.0 && git push origin v1.0.0`). Image: `us-central1-docker.pkg.dev/milestone1-tzuyu/docker/ml-service:v1.0.0`.

## 5. Versioning strategy (semantic versioning)

- **Format**: `vX.Y.Z` (e.g. `v1.0.0`).
- **When**: Create a Git tag for each release; CI builds and pushes the image with that tag.
- **Usage**: Pull by tag for reproducible deployments (e.g. `ml-service:v1.0.0`).

## 6. Troubleshooting

| Issue | What to do |
|-------|------------|
| Image push fails (auth) | Ensure **GCP_SA_KEY** in GitHub Secrets contains the full JSON key of `artifact-registry-push`. In GCP, give the service account **Artifact Registry Writer** on the repo. Ensure the Artifact Registry repository exists (e.g. `docker` in `us-central1`). |
| Tests pass locally, fail in CI | Run tests from `module3/milestone2`: `cd module3/milestone2 && pytest tests/ -v`. Ensure no hardcoded paths; use `MODEL_PATH` and conftest so model is found. |
| Model not found in container | In Dockerfile, `COPY app/ .` must include `model.pkl`. Re-run training and ensure `app/model.pkl` exists before `docker build`. |
| Image too large | Keep multi-stage; use `slim` base; avoid extra system packages. Optionally try Alpine and compare. |
| Build slow | Use layer order (deps then code), `.dockerignore` to exclude `.git`, `tests`, etc., and GHA cache (cache-from/cache-to: gha). |
