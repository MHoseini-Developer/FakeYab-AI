import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights


class CNNLSTMTransformer(nn.Module):
    def __init__(self, pretrained=True, img_size=224, use_pos=True):
        super().__init__()

        weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        resnet = resnet18(weights=weights)

        self.cnn = nn.Sequential(
            resnet.conv1,
            resnet.bn1,
            resnet.relu,
            resnet.maxpool,
            resnet.layer1,
            resnet.layer2,
            resnet.layer3,
            resnet.layer4,
        )

        self.lstm = nn.LSTM(
            input_size=512,
            hidden_size=256,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )

        seq_len = (img_size // 32) ** 2

        self.use_pos = use_pos

        if use_pos:
            self.pos = nn.Parameter(
                torch.zeros(1, seq_len, 512)
            )
            nn.init.trunc_normal_(self.pos, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=2048,
            dropout=0.1,
            batch_first=True,
            norm_first=True,
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2,
        )

        self.norm = nn.LayerNorm(512)

        self.classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 2),
        )

    def forward(self, x):
        x = self.cnn(x)

        x = x.flatten(2).transpose(1, 2)

        x, _ = self.lstm(x)

        if self.use_pos:
            x = x + self.pos[:, :x.size(1)]

        x = self.transformer(x)

        x = self.norm(x.mean(dim=1))

        return self.classifier(x)