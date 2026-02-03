"""
Train a scikit-learn model and save as model.pkl.
Run once to generate the model artifact for the API.
Reproducible: fixed random_state for deterministic training.
"""
import os
import joblib
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Reproducibility: fixed seed
RANDOM_STATE = 42

def main():
    data = load_iris()
    X, y = data.data, data.target
    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    model = RandomForestClassifier(n_estimators=10, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    out_path = os.environ.get("MODEL_PATH", "model.pkl")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    joblib.dump(model, out_path)
    print(f"Model saved to {out_path}")
    print("Class names (indices):", list(data.target_names))

if __name__ == "__main__":
    main()
