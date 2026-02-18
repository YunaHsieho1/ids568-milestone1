# Multi-stage build: builder + minimal runtime (Milestone 2)
# Layer order: least to most frequently changing for cache optimization

# --- Builder stage: install dependencies only ---
FROM python:3.11-slim AS builder
WORKDIR /build

# Dependencies first (change less often than app code)
COPY app/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Runtime stage: minimal image for serving ---
FROM python:3.11-slim
WORKDIR /app

# Copy only installed packages from builder (no build tools)
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Application and model (change more often; keep layer after deps)
COPY app/ .

# Non-root user would go here in production; using default for compatibility
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
