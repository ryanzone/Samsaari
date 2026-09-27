import base64
import requests
from pathlib import Path
from collections import Counter

DATASET = Path("paddy-field-1/valid")
API = "http://127.0.0.1:8080/api/v1/disease-test"

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

results = []

for expected in CLASSES:
    folder = DATASET / expected

    images = [
        p for p in folder.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]

    print(f"{expected}: {len(images)} images")

    for image in images:
        try:
            encoded = base64.b64encode(
                image.read_bytes()
            ).decode("utf-8")

            response = requests.post(
                API,
                json={"image_base64": encoded},
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            results.append({
                "expected": expected,
                "predicted": data["disease"],
                "confidence": data["confidence"],
                "uncertain": data["uncertain"],
                "file": image.name
            })

        except Exception as e:
            print(f"ERROR {image.name}: {e}")


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("SAMSAARI V2 CLASSIFIER TEST")
print("=" * 80)

total = len(results)
correct = sum(
    r["expected"] == r["predicted"]
    for r in results
)

print(f"Total tested : {total}")
print(f"Correct      : {correct}")
print(f"Wrong        : {total - correct}")

if total:
    print(f"Accuracy     : {correct / total * 100:.2f}%")

# ---------------------------------------------------------
# PER CLASS
# ---------------------------------------------------------

print("\nPER CLASS")
print("-" * 80)

for cls in CLASSES:
    rows = [
        r for r in results
        if r["expected"] == cls
    ]

    if not rows:
        continue

    good = sum(
        r["expected"] == r["predicted"]
        for r in rows
    )

    print(
        f"{cls:30} "
        f"{good}/{len(rows)} "
        f"({good / len(rows) * 100:.1f}%)"
    )

# ---------------------------------------------------------
# CONFUSION MATRIX
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("CONFUSION MATRIX")
print("=" * 80)

matrix = {
    expected: Counter()
    for expected in CLASSES
}

for r in results:
    matrix[r["expected"]][r["predicted"]] += 1

print(f"{'Expected':30}", end="")

for cls in CLASSES:
    print(f"{cls[:10]:>12}", end="")

print()

for expected in CLASSES:
    print(f"{expected:30}", end="")

    for predicted in CLASSES:
        print(
            f"{matrix[expected][predicted]:>12}",
            end=""
        )

    print()

# ---------------------------------------------------------
# WRONG PREDICTIONS
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("WRONG PREDICTIONS")
print("=" * 80)

wrong = [
    r for r in results
    if r["expected"] != r["predicted"]
]

for r in wrong:
    status = "[UNCERTAIN]" if r["uncertain"] else ""

    print(
        f"{r['expected']:30} -> "
        f"{r['predicted']:30} "
        f"{r['confidence'] * 100:6.2f}% "
        f"{status} "
        f"{r['file']}"
    )

print("\n" + "=" * 80)