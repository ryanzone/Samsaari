import random
import shutil
from pathlib import Path
from PIL import Image

SOURCE = Path("paddy-field-1/valid")
DEST = Path("test_30")

CLASSES = [
    "bacterial_leaf_blight",
    "bacterial_leaf_streak",
    "bacterial_panicle_blight",
    "blast",
    "brown_spot",
    "dead_heart",
    "downy_mildew",
    "hispa",
    "normal",
    "tungro",
]

IMAGES_PER_CLASS = 30
SEED = 42

random.seed(SEED)

DEST.mkdir(exist_ok=True)

total = 0

for class_name in CLASSES:
    source_dir = SOURCE / class_name
    dest_dir = DEST / class_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    valid_images = []

    for file in source_dir.iterdir():
        if not file.is_file():
            continue

        try:
            with Image.open(file) as img:
                img.verify()
            valid_images.append(file)
        except Exception:
            print(f"Skipping invalid image: {file}")

    if len(valid_images) < IMAGES_PER_CLASS:
        raise RuntimeError(
            f"{class_name}: only {len(valid_images)} valid images available"
        )

    selected = random.sample(valid_images, IMAGES_PER_CLASS)

    for image in selected:
        shutil.copy2(image, dest_dir / image.name)

    print(f"{class_name}: {len(selected)} images")
    total += len(selected)

print(f"\nDONE: {total} images copied to {DEST}")