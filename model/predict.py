"""
اسکریپت inference مستقل برای سایت/بک‌اند — نسخه ۳ (multi-crop).

فایل‌های لازم کنار این اسکریپت: config.json و model_weights.pth
(هر دو را نوت‌بوک Training_v3_multigen در پوشه‌ی genimage_deploy_v4 می‌سازد).

    from predict import DeployedDetector
    detector = DeployedDetector("config.json", "model_weights.pth")
    result = detector.predict_bytes(uploaded_file_bytes)

توابع پیش‌پردازش (ensure_min_side / cap_short_side / crop_at / compute_freq_tensor)
باید عیناً با نوت‌بوک آموزش یکی بمانند. دستی تغییرشان ندهید.

برای مقایسه‌ی دقیق با ارزیابی نوت‌بوک، n_crops=1 بدهید (فقط crop مرکزی).
"""

import io
import json
import time

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageOps
from torchvision import transforms
from torchvision.models import resnet18


class HybridCNNFFTTransformer(nn.Module):
    def __init__(self, num_classes=2, d_model=128, nhead=4,
                 num_transformer_layers=2, dim_feedforward=256, dropout=0.1):
        super().__init__()
        resnet = resnet18(weights=None)
        self.spatial_backbone = nn.Sequential(
            resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool,
            resnet.layer1, resnet.layer2, resnet.layer3, resnet.layer4)
        self.spatial_proj = nn.Linear(512, d_model)

        self.freq_branch = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=2, padding=1), nn.BatchNorm2d(16), nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, 3, stride=2, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, stride=2, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.Conv2d(64, d_model, 3, stride=2, padding=1), nn.BatchNorm2d(d_model), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1))

        self.pos_embed = nn.Parameter(torch.zeros(1, 49 + 1, d_model))

        enc = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward,
                                         dropout=dropout, batch_first=True, norm_first=True)
        self.transformer = nn.TransformerEncoder(enc, num_layers=num_transformer_layers)
        self.norm = nn.LayerNorm(d_model)
        self.classifier = nn.Sequential(nn.Linear(d_model, d_model), nn.ReLU(inplace=True),
                                        nn.Dropout(dropout), nn.Linear(d_model, num_classes))

    def forward(self, rgb, freq):
        s = self.spatial_backbone(rgb).flatten(2).transpose(1, 2)
        s = self.spatial_proj(s)
        f = self.freq_branch(freq).flatten(1).unsqueeze(1)
        x = torch.cat([s, f], dim=1) + self.pos_embed
        x = self.transformer(x)
        return self.classifier(self.norm(x.mean(dim=1)))


def ensure_min_side(img, size):
    w, h = img.size
    if min(w, h) < size:
        s = size / min(w, h)
        img = img.resize((max(size, round(w * s)), max(size, round(h * s))), Image.BICUBIC)
    return img


def cap_short_side(img, max_short):
    w, h = img.size
    if min(w, h) > max_short:
        s = max_short / min(w, h)
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return img


def crop_at(img, size, fx, fy):
    w, h = img.size
    x = int(round((w - size) * fx))
    y = int(round((h - size) * fy))
    return img.crop((x, y, x + size, y + size))


def compute_freq_tensor(crop, eps):
    gray = crop.convert("L")
    arr = torch.from_numpy(np.array(gray, dtype=np.float32) / 255.0).unsqueeze(0)
    f = torch.fft.fftshift(torch.fft.fft2(arr), dim=(-2, -1))
    mag = torch.log1p(torch.abs(f))
    return (mag - mag.mean()) / (mag.std() + eps)


class DeployedDetector:
    def __init__(self, config_path="config.json", weights_path="model_weights.pth",
                 device="cpu", n_crops=None):
        with open(config_path, "r", encoding="utf-8") as fh:
            self.cfg = json.load(fh)

        self.device = torch.device(device)
        self.size = self.cfg["img_size"]
        self.max_short = self.cfg["max_short_side"]
        self.eps = self.cfg["freq_eps"]
        self.fake_idx = self.cfg["fake_idx"]
        self.real_idx = self.cfg["real_idx"]
        self.names = self.cfg["class_names"]
        self.threshold = self.cfg.get("fake_threshold", 0.5)

        fracs = [tuple(x) for x in self.cfg["crop_fracs"]]
        n = n_crops if n_crops is not None else self.cfg["n_crops"]
        self.fracs = fracs[:max(1, min(n, len(fracs)))]

        self.to_tensor_norm = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(self.cfg["mean"], self.cfg["std"]),
        ])

        self.model = HybridCNNFFTTransformer(d_model=self.cfg["d_model"])
        self.model.load_state_dict(torch.load(weights_path, map_location=self.device, weights_only=True))
        self.model.eval().to(self.device)

    @torch.no_grad()
    def predict_pil(self, pil_img):
        t0 = time.time()
        # هر ورودی (RGBA / grayscale / CMYK / چرخش EXIF) اول به RGB استاندارد تبدیل می‌شود
        img = ImageOps.exif_transpose(pil_img).convert("RGB")
        img = cap_short_side(ensure_min_side(img, self.size), self.max_short)

        crops = [crop_at(img, self.size, fx, fy) for fx, fy in self.fracs]
        rgb = torch.stack([self.to_tensor_norm(c) for c in crops]).to(self.device)
        freq = torch.stack([compute_freq_tensor(c, self.eps) for c in crops]).to(self.device)

        probs = torch.softmax(self.model(rgb, freq), dim=1).mean(dim=0)
        fake_p = float(probs[self.fake_idx])
        real_p = float(probs[self.real_idx])
        is_fake = fake_p >= self.threshold

        return {
            "label": self.names[self.fake_idx] if is_fake else self.names[self.real_idx],
            "is_fake": bool(is_fake),
            "fake_probability": round(fake_p, 4),
            "real_probability": round(real_p, 4),
            "n_crops": len(crops),
            "inference_ms": round((time.time() - t0) * 1000, 1),
        }

    def predict_path(self, path):
        with Image.open(path) as im:
            return self.predict_pil(im)

    def predict_bytes(self, raw_bytes):
        with Image.open(io.BytesIO(raw_bytes)) as im:
            return self.predict_pil(im)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("استفاده: python predict.py path/to/image.jpg")
        sys.exit(1)

    BASE_DIR = Path(__file__).resolve().parent

    config_path = BASE_DIR / "config.json"
    weights_path = BASE_DIR / "model_weights.pth"

    detector = DeployedDetector(
        config_path=str(config_path),
        weights_path=str(weights_path),
        device="cpu"
    )

    result = detector.predict_path(sys.argv[1])

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    ))
