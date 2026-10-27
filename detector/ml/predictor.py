import torch
from pathlib import Path

from .model import CNNLSTMTransformer


BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "model" / "best.pth"


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model():
    model = CNNLSTMTransformer(
        pretrained=False,
        img_size=224,
        use_pos=True,
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(checkpoint["model_state_dict"])

    model.to(device)
    model.eval()

    return model