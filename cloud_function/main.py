"""
Milestone 1: Google Cloud Function - same prediction logic as FastAPI.
Stateless: each invocation may load the model (cold start) or reuse instance (warm).
"""
import os
import joblib
import functions_framework

# Class names for Iris (must match FastAPI)
CLASS_NAMES = ["setosa", "versicolor", "virginica"]

# Module-level cache: warm instances reuse loaded model (lifecycle: cold vs warm)
_model = None


def _load_model():
    """Load model once per instance (reused on warm invocations)."""
    global _model
    if _model is not None:
        return _model
    # Cloud Function: model next to main.py in deployed package
    path = os.path.join(os.path.dirname(__file__), "model.pkl")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Model not found at {path}. Add model.pkl to cloud_function/ before deploy.")
    _model = joblib.load(path)
    return _model


@functions_framework.http
def predict(request):
    """
    HTTP-triggered function. Same contract as FastAPI /predict:
    JSON body: { "sepal_length", "sepal_width", "petal_length", "petal_width" }
    Returns: { "predicted_class", "label" }
    """
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    try:
        data = request.get_json(silent=True) or {}
        features = [
            float(data.get("sepal_length", 0)),
            float(data.get("sepal_width", 0)),
            float(data.get("petal_length", 0)),
            float(data.get("petal_width", 0)),
        ]
    except (TypeError, ValueError) as e:
        return ({"error": f"Invalid request body: {e}"}, 400)

    try:
        model = _load_model()
    except FileNotFoundError as e:
        return ({"error": str(e)}, 503)

    pred_index = int(model.predict([features])[0])
    if pred_index < 0 or pred_index >= len(CLASS_NAMES):
        return ({"error": "Invalid model output"}, 500)

    return (
        {
            "predicted_class": pred_index,
            "label": CLASS_NAMES[pred_index],
        },
        200,
        {"Content-Type": "application/json"},
    )
