import base64
import json
import requests
from pathlib import Path

TEST_DIR = Path("test_30")
API_URL = "http://127.0.0.1:8080/api/v1/simulate"

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

for disease in CLASSES:
    images = list((TEST_DIR / disease).glob("*"))

    if not images:
        print(f"[SKIP] {disease}: no image")
        continue

    image = images[0]

    with open(image, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode()

    payload = {
        "engine": "samsaari-v2",
        "timestamp": "2026-09-27T00:00:00Z",

        "farm_profile": {
            "crop": "rice",
            "area_acres": 2,
            "growth_stage": "vegetative"
        },

        "geospatial_telemetry": {
            "latitude": 12.84,
            "longitude": 80.07
        },

        "meteorological_risk": {
            "rainfall_probability": 20,
            "temperature_c": 29,
            "humidity": 75,
            "wind_speed_kmh": 8
        },

        "market_telemetry": {
            "rice_price_per_kg": 35
        },

        "financial_inputs": {
            "spray_cost_inr": 500,
            "estimated_crop_value_inr": 10000
        },

        "image_base64": image_base64
    }

    print(f"\nTesting: {disease}")
    print(f"Image: {image.name}")

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=120
        )

        print("HTTP:", response.status_code)

        if response.ok:
            data = response.json()

            result = {
                "expected": disease,
                "image": image.name,
                "disease": data.get("disease"),
                "confidence": data.get("disease_confidence"),
                "uncertain": data.get("disease_uncertain"),
                "action": data.get("recommended_action"),
                "roi_a": data.get("scenario_a_roi_inr"),
                "roi_b": data.get("scenario_b_roi_inr"),
                "risk": data.get("risk_factor"),
            }

            results.append(result)

            print(json.dumps(result, indent=2))

        else:
            print(response.text)

    except Exception as e:
        print("ERROR:", e)

output = Path("gemini_test_10_results.json")
output.write_text(json.dumps(results, indent=2))

print("\n==============================")
print(f"Finished: {len(results)}/10")
print(f"Saved: {output}")
print("==============================")