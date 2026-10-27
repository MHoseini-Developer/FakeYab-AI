from PIL import Image
from torchvision import transforms


IMG_SIZE = 224

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])


def preprocess_image(image):
    """
    آماده‌سازی تصویر آپلودشده برای ورود به مدل.
    """

    image = image.convert("RGB")

    tensor = eval_transform(image)

    # اضافه کردن batch dimension
    tensor = tensor.unsqueeze(0)

    return tensor