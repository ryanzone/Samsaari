import os
from collections import Counter

import numpy as np
import torch
from datasets import load_dataset, concatenate_datasets
from PIL import Image
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from torch import nn
from torch.utils.data import DataLoader
from torchvision import transforms, models


# ============================================================
# CONFIG
# ============================================================

SEED = 42
BATCH_SIZE = 64
IMAGE_SIZE = 224
EPOCHS = 20
LEARNING_RATE = 1e-4

MODEL_PATH = "rice_disease_mobilenetv3_v2.pth"

torch.manual_seed(SEED)
np.random.seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("Samsaari Rice Disease Classifier")
print("=" * 60)

print("\nDevice:", DEVICE)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print(
        "VRAM:",
        round(
            torch.cuda.get_device_properties(0).total_memory
            / (1024 ** 3),
            2
        ),
        "GB"
    )
else:
    print("WARNING: CUDA is not available.")
    print("Training will run on CPU.")


# ============================================================
# 1. LOAD DATASETS
# ============================================================

print("\nLoading Hugging Face datasets...")

paddy = load_dataset(
    "techharry/paddy_disease_classification"
)["train"]

india_rice = load_dataset(
    "Project-AgML/rice_leaf_disease_classification_india"
)["train"]

print("Paddy Disease:", len(paddy))
print("Indian Rice Disease:", len(india_rice))


# ============================================================
# 2. NORMALIZE LABELS
# ============================================================

paddy_label_names = paddy.features["label"].names
india_label_names = india_rice.features["label"].names


def normalize_india_label(label):

    mapping = {
        "Bacterialblight": "bacterial_leaf_blight",
        "Blast": "blast",
        "Brownspot": "brown_spot",
        "Tungro": "tungro",
    }

    return mapping[label]


paddy_class_names = [
    paddy_label_names[i]
    for i in paddy["label"]
]

india_class_names = [
    normalize_india_label(
        india_label_names[i]
    )
    for i in india_rice["label"]
]


# ============================================================
# 3. UNIFIED CLASSES
# ============================================================

CLASS_NAMES = sorted(
    set(
        paddy_class_names +
        india_class_names
    )
)

CLASS_TO_ID = {
    name: i
    for i, name in enumerate(CLASS_NAMES)
}

print("\nUnified classes:")

for i, name in enumerate(CLASS_NAMES):
    print(f"{i:2d} -> {name}")

print("\nTotal classes:", len(CLASS_NAMES))


# ============================================================
# 4. REMOVE ORIGINAL LABELS
# ============================================================

paddy = paddy.remove_columns(["label"])
india_rice = india_rice.remove_columns(["label"])


# ============================================================
# 5. ADD NORMALIZED CLASS NAME
# ============================================================

paddy = paddy.add_column(
    "class_name",
    paddy_class_names
)

india_rice = india_rice.add_column(
    "class_name",
    india_class_names
)


# ============================================================
# 6. COMBINE DATASETS
# ============================================================

dataset = concatenate_datasets([
    paddy,
    india_rice
])

print("\nCombined dataset:", len(dataset))


# ============================================================
# 7. TRAIN / VALIDATION SPLIT
# ============================================================

indices = np.arange(len(dataset))

train_indices, val_indices = train_test_split(
    indices,
    test_size=0.20,
    random_state=SEED,
    stratify=dataset["class_name"]
)

train_dataset = dataset.select(
    train_indices
)

val_dataset = dataset.select(
    val_indices
)

print("Training images:", len(train_dataset))
print("Validation images:", len(val_dataset))


# ============================================================
# 8. IMAGE TRANSFORMS
# ============================================================

train_transform = transforms.Compose([

    transforms.RandomResizedCrop(
        IMAGE_SIZE,
        scale=(0.65, 1.0),
        ratio=(0.85, 1.15)
    ),

    transforms.RandomHorizontalFlip(p=0.5),

    transforms.RandomVerticalFlip(p=0.3),

    transforms.RandomRotation(20),

    transforms.ColorJitter(
        brightness=0.3,
        contrast=0.3,
        saturation=0.25,
        hue=0.05
    ),

    transforms.RandomAffine(
        degrees=0,
        translate=(0.08, 0.08),
        scale=(0.9, 1.1)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),

    transforms.RandomErasing(
        p=0.15,
        scale=(0.02, 0.12),
        ratio=(0.3, 3.3)
    )
])


val_transform = transforms.Compose([

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
# 9. PYTORCH DATASET
# ============================================================

class RiceDataset(torch.utils.data.Dataset):

    def __init__(
        self,
        hf_dataset,
        transform
    ):
        self.dataset = hf_dataset
        self.transform = transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):

        item = self.dataset[index]

        image = item["image"]

        if not isinstance(
            image,
            Image.Image
        ):
            image = Image.fromarray(
                np.array(image)
            )

        image = image.convert("RGB")

        image = self.transform(image)

        label = CLASS_TO_ID[
            item["class_name"]
        ]

        return image, label


train_data = RiceDataset(
    train_dataset,
    train_transform
)

val_data = RiceDataset(
    val_dataset,
    val_transform
)


# ============================================================
# 10. CLASS DISTRIBUTION
# ============================================================

train_labels = [
    CLASS_TO_ID[label]
    for label in train_dataset["class_name"]
]

class_counts = Counter(
    train_labels
)

print("\nTraining distribution:")

for class_id in range(
    len(CLASS_NAMES)
):

    print(
        f"{CLASS_NAMES[class_id]:30}"
        f"{class_counts[class_id]}"
    )



# ============================================================
# 12. DATALOADERS
# ============================================================
train_loader = DataLoader(
    train_data,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_data,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)


# ============================================================
# 13. MOBILENETV3-LARGE
# ============================================================

print("\nLoading MobileNetV3-Large...")

weights = (
    models.MobileNet_V3_Large_Weights.DEFAULT
)

model = models.mobilenet_v3_large(
    weights=weights
)

# Replace final classifier layer
num_features = (
    model.classifier[-1].in_features
)

model.classifier[-1] = nn.Linear(
    num_features,
    len(CLASS_NAMES)
)

model = model.to(DEVICE)

print("Model loaded.")


# ============================================================
# 14. LOSS + OPTIMIZER
# ============================================================

# Class-weighted loss
total_samples = len(train_labels)
num_classes = len(CLASS_NAMES)

class_weights = torch.tensor(
    [
        total_samples / (num_classes * class_counts[i])
        for i in range(num_classes)
    ],
    dtype=torch.float32
).to(DEVICE)

print("\nClass weights:")

for i, weight in enumerate(class_weights):
    print(
        f"{CLASS_NAMES[i]:30} "
        f"{weight.item():.4f}"
    )

criterion = nn.CrossEntropyLoss(
    weight=class_weights,
    label_smoothing=0.1
)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2
)


# ============================================================
# 15. TRAINING
# ============================================================
best_val_f1 = 0.0

print("\n" + "=" * 60)
print("STARTING TRAINING")
print("=" * 60)


for epoch in range(EPOCHS):

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model.train()

    running_loss = 0.0
    train_correct = 0
    train_total = 0

    for batch_index, (
        images,
        labels
    ) in enumerate(train_loader):

        images = images.to(
            DEVICE,
            non_blocking=True
        )

        labels = labels.to(
            DEVICE,
            non_blocking=True
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        outputs = model(images)

        loss = criterion(
            outputs,
            labels
        )

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

        predictions = outputs.argmax(
            dim=1
        )

        train_correct += (
            predictions == labels
        ).sum().item()

        train_total += labels.size(0)

    train_loss = (
        running_loss /
        len(train_loader)
    )

    train_accuracy = (
        train_correct /
        train_total
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    model.eval()

    val_correct = 0
    val_total = 0

    all_predictions = []
    all_labels = []

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(
                DEVICE,
                non_blocking=True
            )

            labels = labels.to(
                DEVICE,
                non_blocking=True
            )

            outputs = model(images)

            predictions = outputs.argmax(
                dim=1
            )

            val_correct += (
                predictions == labels
            ).sum().item()

            val_total += labels.size(0)

            all_predictions.extend(
                predictions.cpu().numpy()
            )

            all_labels.extend(
                labels.cpu().numpy()
            )

    val_accuracy = (
        val_correct /
        val_total
    )

    val_macro_f1 = f1_score(
    all_labels,
    all_predictions,
    average="macro"
)
    scheduler.step(val_macro_f1)


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print(
        f"\nEpoch {epoch + 1}/{EPOCHS}"
    )

    print(
        f"Loss       : {train_loss:.4f}"
    )

    print(
        f"Train Acc  : {train_accuracy:.4f}"
    )

    print(
        f"Val Acc    : {val_accuracy:.4f}"
    )

    print(
        f"LR         : "
        f"{optimizer.param_groups[0]['lr']:.7f}"
    )


    # --------------------------------------------------------
    # SAVE BEST MODEL
    # --------------------------------------------------------

if val_macro_f1 > best_val_f1:

    best_val_f1 = val_macro_f1

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "class_names": CLASS_NAMES,
            "image_size": IMAGE_SIZE,
            "model": "mobilenet_v3_large",
            "best_val_f1": best_val_f1,
            "best_val_accuracy": val_accuracy
        },
        MODEL_PATH
    )

    print(
        f"✓ Best model saved "
        f"(F1: {val_macro_f1:.4f}, "
        f"Accuracy: {val_accuracy:.4f})"
    )
    print(
    f"Val Macro F1: {val_macro_f1:.4f}"
)


# ============================================================
# 16. FINAL EVALUATION
# ============================================================

print("\n" + "=" * 60)
print("FINAL EVALUATION")
print("=" * 60)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()

all_predictions = []
all_labels = []

with torch.no_grad():

    for images, labels in val_loader:

        images = images.to(
            DEVICE,
            non_blocking=True
        )

        outputs = model(images)

        predictions = outputs.argmax(
            dim=1
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )

        all_labels.extend(
            labels.numpy()
        )


print("\nClassification Report:\n")

print(
    classification_report(
        all_labels,
        all_predictions,
        target_names=CLASS_NAMES,
        zero_division=0
    )
)


print("\nConfusion Matrix:\n")

print(
    confusion_matrix(
        all_labels,
        all_predictions
    )
)


# ============================================================
# 17. COMPLETE
# ============================================================

print("\n" + "=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print(
    f"Best validation accuracy: "
    f"{checkpoint['best_val_accuracy']:.4f}"
)

print(
    f"Best validation Macro F1: "
    f"{best_val_f1:.4f}"
)

print(
    f"Model saved to: {MODEL_PATH}"
)

print(
    f"Classes: {len(CLASS_NAMES)}"
)

if torch.cuda.is_available():

    print(
        f"GPU used: "
        f"{torch.cuda.get_device_name(0)}"
    )

    print(
        f"Peak GPU memory: "
        f"{torch.cuda.max_memory_allocated() / (1024 ** 3):.2f} GB"
    )