import requests
import io
import pygame

SIMULATE_URL = "http://127.0.0.1:8080/api/v1/simulate"
TTS_URL = "http://127.0.0.1:8080/api/v1/tts"

# Your test image
image_path = r"test_30\blast\100367_jpg.rf.88dde607ee63d48fa3137f99da90e4c6.jpg"

# ------------------------------------------------------------
# 1. Send simulation
# ------------------------------------------------------------

import base64

with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

simulate_payload = {
    "engine": "Krishi-Twin-Decision-Core",
    "timestamp": "2026-09-27T14:00:00Z",

    "farm_profile": {
        "coordinates": {
            "latitude": 12.84,
            "longitude": 80.07
        },
        "crop": "Rice",
        "farm_size_acres": 2,
        "detected_symptom": "Blast"
    },

    "geospatial_telemetry": {
        "mean_ndvi_index": 0.5713,
        "canopy_vigor": "Healthy"
    },

    "meteorological_risk": {
        "rainfall_probability": 54,
        "rain_next_24h_mm": 0.4,
        "wind_speed_kmh": 16.8,
        "washoff_risk": "LOW"
    },

    "market_telemetry": {
        "price_inr_per_kg": 21.0,
        "source": "baseline"
    },

    "financial_inputs": {
        "spray_cost_inr": 850,
        "potential_crop_loss_inr": 4200
    },

    "image_base64": image_base64
}

response = requests.post(
    SIMULATE_URL,
    json=simulate_payload,
    timeout=120
)

response.raise_for_status()

simulation = response.json()

voice_text = simulation["voice_script_2_sentences"]

print("\nDecision:", simulation["recommended_action"])
print("Voice:", voice_text)

# ------------------------------------------------------------
# 2. Get coordinates dynamically from same payload
# ------------------------------------------------------------

coordinates = simulate_payload["farm_profile"]["coordinates"]

# ------------------------------------------------------------
# 3. Send dynamic voice text + coordinates to TTS
# ------------------------------------------------------------

tts_payload = {
    "text": voice_text,
    "latitude": coordinates["latitude"],
    "longitude": coordinates["longitude"]
}

tts_response = requests.post(
    TTS_URL,
    json=tts_payload,
    timeout=120
)

tts_response.raise_for_status()

print(
    "Language:",
    tts_response.headers.get("X-Resolved-Language")
)

print(
    "Audio bytes:",
    len(tts_response.content)
)

# ------------------------------------------------------------
# 4. Play MP3 directly in terminal
# ------------------------------------------------------------

pygame.mixer.init()

pygame.mixer.music.load(
    io.BytesIO(tts_response.content)
)

pygame.mixer.music.play()

print("Playing audio...")

while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)

pygame.mixer.quit()

print("Done.")