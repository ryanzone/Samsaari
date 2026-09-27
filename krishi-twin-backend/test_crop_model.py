import sys
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms, models
from torch import nn


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "rice_disease_mobilenetv3_v2.pth"
IMAGE_SIZE = 224

# Below this confidence, don't give a hard diagnosis.
CONFIDENCE_THRESHOLD = 0.70

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading model...")

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE
)

CLASS_NAMES = checkpoint["class_names"]

model = models.mobilenet_v3_large(
    weights=None
)

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


print("Device:", DEVICE)

if torch.cuda.is_available():
    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

print("Classes:", len(CLASS_NAMES))


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

transform = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],
        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_image(image_path):

    image_path = Path(image_path)

    if not image_path.exists():

        print(
            f"\nERROR: Image not found:"
            f"\n{image_path}"
        )

        return

    try:

        image = Image.open(
            image_path
        ).convert("RGB")

    except Exception as e:

        print(
            "\nERROR: Could not open image:"
        )

        print(e)

        return


    image_tensor = transform(
        image
    ).unsqueeze(0)

    image_tensor = image_tensor.to(
        DEVICE
    )


    # --------------------------------------------------------
    # INFERENCE
    # --------------------------------------------------------

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )[0]


    # --------------------------------------------------------
    # TOP 3
    # --------------------------------------------------------

    top_probabilities, top_indices = torch.topk(
        probabilities,
        k=min(3, len(CLASS_NAMES))
    )


    top_results = []

    for probability, index in zip(
        top_probabilities,
        top_indices
    ):

        class_name = CLASS_NAMES[
            index.item()
        ]

        confidence = (
            probability.item() * 100
        )

        top_results.append(
            (
                class_name,
                confidence
            )
        )


    prediction = top_results[0][0]
    confidence = top_results[0][1]


    # ========================================================
    # RESULT
    # ========================================================

    print("\n" + "=" * 60)
    print("SAMSAA RI CROP SCAN")
    print("=" * 60)

    print(
        f"\nPrediction : {prediction}"
    )

    print(
        f"Confidence : {confidence:.2f}%"
    )


    if confidence < (
        CONFIDENCE_THRESHOLD * 100
    ):

        print(
            "\nStatus     : UNCERTAIN"
        )

        print(
            "The model is not confident "
            "enough to provide a diagnosis."
        )

    elif prediction == "normal":

        print(
            "\nStatus     : HEALTHY"
        )

    else:

        print(
            "\nStatus     : DISEASE DETECTED"
        )


    # ========================================================
    # TOP 3
    # ========================================================

    print("\nTop 3 predictions:")

    for rank, (
        class_name,
        confidence
    ) in enumerate(
        top_results,
        start=1
    ):

        print(
            f"{rank}. "
            f"{class_name:<30}"
            f"{confidence:.2f}%"
        )


    print("\n" + "=" * 60)


# ============================================================
# COMMAND LINE
# ============================================================

if len(sys.argv) < 2:

    print("\nUsage:")

    print(
        "python test_crop_model.py "
        "<image_path>"
    )

    print("\nExample:")

    print(
        "python test_crop_model.py "
        "test_images/rice.jpg"
    )

    sys.exit(1)


image_path = sys.argv[1]

predict_image(image_path)