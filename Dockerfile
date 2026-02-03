# Milestone 1 - Cloud Run container
# Reproducible: pinned base image and install from requirements.txt
FROM python:3.11-slim

WORKDIR /app

# Install dependencies (reproducible versions)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application and model artifact
COPY main.py .
COPY model.pkl .

# Cloud Run expects PORT env (default 8080)
ENV PORT=8080
EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
