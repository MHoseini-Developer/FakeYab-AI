
from pathlib import Path
import json

from model.predict import DeployedDetector

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
IMAGE_PATH = BASE_DIR / "test_real.jpg"

for n_crops in (1, 5):
    detector = DeployedDetector(
        config_path=str(MODEL_DIR / "config.json"),
        weights_path=str(MODEL_DIR / "model_weights.pth"),
        device="cpu",
        n_crops=n_crops,
    )

    result = detector.predict_path(str(IMAGE_PATH))

    print(f"\n--- n_crops={n_crops} ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
