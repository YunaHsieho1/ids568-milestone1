# Pytest conftest: path and env for app + model
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# So lifespan can find model when running from module3/milestone2
if "MODEL_PATH" not in os.environ:
    os.environ["MODEL_PATH"] = os.path.join(
        os.path.dirname(__file__), "app", "model.pkl"
    )
