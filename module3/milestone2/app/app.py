"""
Milestone 2: ML inference service (from Milestone 1).
Lifecycle: Input (HTTP) → Schema validation → Model (artifact) → API response → Consumer.
"""
import os
from contextlib import asynccontextmanager
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

# --- Pydantic schemas ---
class PredictRequest(BaseModel):
    """Request: 4 features for Iris model."""
    sepal_length: float = Field(..., ge=0, le=10, description="Sepal length in cm")
    sepal_width: float = Field(..., ge=0, le=10, description="Sepal width in cm")
    petal_length: float = Field(..., ge=0, le=10, description="Petal length in cm")
    petal_width: float = Field(..., ge=0, le=10, description="Petal width in cm")


class PredictResponse(BaseModel):
    """Response: predicted class index and label."""
    predicted_class: int = Field(..., description="Predicted class index (0=setosa, 1=versicolor, 2=virginica)")
    label: str = Field(..., description="Human-readable class name")


CLASS_NAMES = ["setosa", "versicolor", "virginica"]
_model = None


def load_model():
    """Load model from MODEL_PATH or default model.pkl (relative to /app)."""
    global _model
    path = os.environ.get("MODEL_PATH", "model.pkl")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Model not found at {path}. Run training first.")
    _model = joblib.load(path)
    return _model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model once at startup."""
    load_model()
    yield


app = FastAPI(
    title="Milestone 2 - ML Inference API",
    description="Containerized scikit-learn model serving with /predict endpoint.",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check for load balancers and CI."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """Predict Iris class from 4 features."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    features = [[req.sepal_length, req.sepal_width, req.petal_length, req.petal_width]]
    pred_index = int(_model.predict(features)[0])
    if pred_index < 0 or pred_index >= len(CLASS_NAMES):
        raise HTTPException(status_code=500, detail="Invalid model output")
    return PredictResponse(
        predicted_class=pred_index,
        label=CLASS_NAMES[pred_index],
    )
