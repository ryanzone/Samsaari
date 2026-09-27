import base64
import requests
from pathlib import Path

# -----------------------------
# TEST IMAGE
# -----------------------------
IMAGE_PATH = Path("test/test2.jpg")
EXPECTED_DISEASE = "blast"

# -----------------------------
# CHECK IMAGE
# -----------------------------
if not IMAGE_PATH.exists():
    print(f"ERROR: Image not found: {IMAGE_PATH.resolve()}")
    raise SystemExit(1)

print("=" * 50)
print("SAMSAA RI V2 DISEASE TEST")
print("=" * 50)
print(f"Image:    {IMAGE_PATH}")
print(f"Expected: {EXPECTED_DISEASE}")
print()

# -----------------------------
# ENCODE IMAGE
# -----------------------------
image_base64 = base64.b64encode(
    IMAGE_PATH.read_bytes()
).decode("utf-8")

# -----------------------------
# REQUEST
# -----------------------------
payload = {
    "engine": "samsaari",
    "timestamp": "2026-09-27T01:00:00+05:30",

    "farm_profile": {
        "crop": "Rice (Paddy)",
        "detected_symptom": "Unknown"
    },

    "geospatial_telemetry": {
        "mean_ndvi_index": 0.65,
        "canopy_vigor": "Healthy"
    },

    "meteorological_risk": {
        "rain_next_24h_mm": 5,
        "rain_probability_pct": 30,
        "computed_washoff_risk": "LOW"
    },

    "market_telemetry": {},

    "financial_inputs": {
        "spray_cost_inr": 800,
        "potential_crop_loss_inr": 3500
    },

    "image_base64": image_base64
}

print("Sending image to Samsaari...")
print()

response = requests.post(
    "http://127.0.0.1:8080/api/v1/simulate",
    json=payload,
    timeout=120
)

response.raise_for_status()
result = response.json()

# -----------------------------
# RESULT
# -----------------------------
disease = result.get("disease")
confidence = result.get("disease_confidence")
uncertain = result.get("disease_uncertain")

print("=" * 50)
print("RESULT")
print("=" * 50)

print(f"Disease:       {disease}")
print(f"Confidence:    {confidence * 100:.2f}%")
print(f"Uncertain:     {uncertain}")
print(f"Action:        {result.get('recommended_action')}")
print(f"Scenario A:    ₹{result.get('scenario_a_roi_inr')}")
print(f"Scenario B:    ₹{result.get('scenario_b_roi_inr')}")
print()

# -----------------------------
# EXPECTED VS ACTUAL
# -----------------------------
print("=" * 50)
print("MODEL CHECK")
print("=" * 50)

if disease == EXPECTED_DISEASE:
    print("PASS: Model predicted BLAST")
else:
    print(f"MISS: Expected BLAST, got {disease}")

if confidence is not None:
    if confidence >= 0.70:
        print("Confidence: HIGH")
    else:
        print("Confidence: UNCERTAIN (<70%)")

print("=" * 50)