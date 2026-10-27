
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"

CONFIG_PATH = MODEL_DIR / "config.json"
WEIGHTS_PATH = MODEL_DIR / "model_weights.pth"

_detector = None


def get_detector():
    global _detector

    if _detector is None:
        from model.predict import DeployedDetector

        _detector = DeployedDetector(
            config_path=str(CONFIG_PATH),
            weights_path=str(WEIGHTS_PATH),
            device="cpu",
        )

    return _detector


def predict(image_bytes):
    detector = get_detector()
    return detector.predict_bytes(image_bytes)
