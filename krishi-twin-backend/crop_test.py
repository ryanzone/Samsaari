import sys
import torch
from PIL import Image
from torchvision import transforms, models
from torch import nn

# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "rice_disease_mobilenetv3_v2.pth"
IMAGE_SIZE = 224
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================================
# LOAD MODEL
# ============================================================

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE
)

CLASS_NAMES = checkpoint["class_names"]

model = models.mobilenet_v3_large(weights=None)

num_features = model.classifier[-1].in_features

model.classifier[-1] = nn.Linear(
    num_features,
    len(CLASS_NAMES)
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model = model.to(DEVICE)
model.eval()

# ============================================================
# TRANSFORM
# ============================================================

transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ============================================================
# PREDICT
# ============================================================

def predict(image, name):

    image = image.convert("RGB")

    tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output = model(tensor)
        probabilities = torch.softmax(output, dim=1)[0]

    values, indices = torch.topk(
        probabilities,
        3
    )

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    for rank, (value, index) in enumerate(
        zip(values, indices),
        start=1
    ):
        print(
            f"{rank}. "
            f"{CLASS_NAMES[index.item()]:30} "
            f"{value.item() * 100:.2f}%"
        )


# ============================================================
# CENTER SQUARE CROP
# ============================================================

def center_square(image, fraction):

    width, height = image.size

    side = int(
        min(width, height) * fraction
    )

    left = (width - side) // 2
    top = (height - side) // 2

    right = left + side
    bottom = top + side

    return image.crop(
        (left, top, right, bottom)
    )


# ============================================================
# MAIN
# ============================================================

if len(sys.argv) != 2:

    print(
        "Usage: python crop_test.py "
        "test_images/rice.jpg"
    )

    sys.exit(1)


image_path = sys.argv[1]

image = Image.open(image_path)

print("=" * 60)
print("SAMS AARI FRAMING TEST")
print("=" * 60)

print("Image:", image_path)
print("Original size:", image.size)

# Original image
predict(
    image,
    "ORIGINAL IMAGE"
)

# 80% center square
crop80 = center_square(
    image,
    0.80
)

predict(
    crop80,
    "CENTER CROP - 80%"
)

# 60% center square
crop60 = center_square(
    image,
    0.60
)

predict(
    crop60,
    "CENTER CROP - 60%"
)

# 40% center square
crop40 = center_square(
    image,
    0.40
)

predict(
    crop40,
    "CENTER CROP - 40%"
)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)