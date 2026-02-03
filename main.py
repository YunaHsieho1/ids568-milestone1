"""
Milestone 1: FastAPI model serving microservice.
Lifecycle: Input (HTTP) → Schema validation → Model (artifact) → API response → Consumer.
"""
import os
from contextlib import asynccontextmanager
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# --- Pydantic schemas (schema validation for API) ---
class PredictRequest(BaseModel):
    """Request body: 4 features for Iris-like model (sepal_length, sepal_width, petal_length, petal_width)."""
    sepal_length: float = Field(..., ge=0, le=10, description="Sepal length in cm")
    sepal_width: float = Field(..., ge=0, le=10, description="Sepal width in cm")
    petal_length: float = Field(..., ge=0, le=10, description="Petal length in cm")
    petal_width: float = Field(..., ge=0, le=10, description="Petal width in cm")


class PredictResponse(BaseModel):
    """Response: predicted class index and label."""
    predicted_class: int = Field(..., description="Predicted class index (0=setosa, 1=versicolor, 2=virginica)")
    label: str = Field(..., description="Human-readable class name")


# Class names for Iris (deterministic mapping)
CLASS_NAMES = ["setosa", "versicolor", "virginica"]

# Global model reference (loaded once at startup for deterministic behavior)
_model = None


def load_model():
    """Load model artifact deterministically from MODEL_PATH or default model.pkl."""
    global _model
    path = os.environ.get("MODEL_PATH", "model.pkl")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Model artifact not found at {path}. Run: python train_model.py"
        )
    _model = joblib.load(path)
    return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model once at startup (lifecycle: startup → ready to serve)."""
    load_model()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="Milestone 1 - Model Serving API",
    description="Scikit-learn model serving with /predict endpoint. Lifecycle: Input → Model → API → Consumer.",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Redirect to interactive API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check for Cloud Run / load balancers."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """
    Predict Iris class from 4 features.
    Request validated by Pydantic; model loaded at startup (deterministic).
    """
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    features = [
        [req.sepal_length, req.sepal_width, req.petal_length, req.petal_width]
    ]
    pred_index = int(_model.predict(features)[0])
    if pred_index < 0 or pred_index >= len(CLASS_NAMES):
        raise HTTPException(status_code=500, detail="Invalid model output")
    return PredictResponse(
        predicted_class=pred_index,
        label=CLASS_NAMES[pred_index],
    )
