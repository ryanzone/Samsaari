import io
import requests
import pygame

from audioPipeline import process_advisory_audio_by_coordinates


# ============================================================
# CONFIGURATION
# ============================================================

MAP_LAT = 9.8821
MAP_LON = 78.0815

BACKEND_URL = "http://localhost:8080/api/v1/simulate"


# ============================================================
# INITIALIZE AUDIO
# ============================================================

pygame.mixer.init()


# ============================================================
# FARM SIMULATION PAYLOAD
# ============================================================

sim_payload = {
    "engine": "Krishi-Twin-Decision-Core",

    "farm_profile": {
        "coordinates": {
            "latitude": MAP_LAT,
            "longitude": MAP_LON
        },
        "crop": "Rice (Paddy)",
        "detected_symptom": "Leaf Blight"
    },

    "geospatial_telemetry": {
        "latitude": MAP_LAT,
        "longitude": MAP_LON,
        "ndvi": 0.37
    },

    "meteorological_risk": {
        "rain_next_24h_mm": 18.5,
        "rain_probability_pct": 95,
        "computed_washoff_risk": "HIGH"
    },

    "financial_inputs": {
        "spray_cost_inr": 850.0,
        "potential_crop_loss_inr": 4200.0
    }
}


# ============================================================
# 1. FETCH AI SIMULATION
# ============================================================

print(
    f"1. Fetching live telemetry simulation "
    f"for coordinates [{MAP_LAT}, {MAP_LON}]..."
)

try:

    sim_response = requests.post(
        BACKEND_URL,
        json=sim_payload,
        timeout=60
    )

except requests.RequestException as exc:

    print(f"Simulation backend error: {exc}")
    pygame.mixer.quit()
    raise SystemExit(1)


if sim_response.status_code != 200:

    print(
        f"Error calling simulation backend: "
        f"{sim_response.status_code} - "
        f"{sim_response.text}"
    )

    pygame.mixer.quit()
    raise SystemExit(1)


# ============================================================
# 2. EXTRACT GEMINI ADVISORY
# ============================================================

try:

    sim_data = sim_response.json()

    dynamic_advisory = sim_data[
        "voice_script_2_sentences"
    ]

except (ValueError, KeyError) as exc:

    print(
        f"Invalid simulation response: {exc}"
    )

    pygame.mixer.quit()
    raise SystemExit(1)


print(
    f'\n[Gemini AI Output]: "{dynamic_advisory}"'
)


# ============================================================
# 3. REGIONAL AUDIO PIPELINE
# ============================================================

print(
    "\n2. Synthesizing audio "
    "for regional map location..."
)

try:

    audio_result = (
        process_advisory_audio_by_coordinates(
            raw_text=dynamic_advisory,
            lat=MAP_LAT,
            lon=MAP_LON
        )
    )

except Exception as exc:

    print(
        f"Audio pipeline error: {exc}"
    )

    pygame.mixer.quit()
    raise SystemExit(1)


print(
    f"Mapped Language Code: "
    f"{audio_result['resolved_language']}"
)

print(
    f"Translated Advisory: "
    f"{audio_result['translated_text']}"
)


# ============================================================
# 4. PLAY GENERATED MP3
# ============================================================

print("\n3. Playing dynamic audio...")

audio_bytes = audio_result["audio_bytes"]

if not isinstance(audio_bytes, bytes):
    print(
        "ERROR: Audio pipeline did not return "
        "binary MP3 data."
    )

    pygame.mixer.quit()
    raise SystemExit(1)


if len(audio_bytes) == 0:
    print(
        "ERROR: Generated audio stream is empty."
    )

    pygame.mixer.quit()
    raise SystemExit(1)


try:

    audio_stream = io.BytesIO(audio_bytes)

    pygame.mixer.music.load(audio_stream)
    pygame.mixer.music.play()

    clock = pygame.time.Clock()

    while pygame.mixer.music.get_busy():
        clock.tick(10)

except pygame.error as exc:

    print(
        f"Audio playback error: {exc}"
    )

    pygame.mixer.quit()
    raise SystemExit(1)


print("Playback complete!")

pygame.mixer.quit()