# Krishi-Twin: Counterfactual Agro-Financial Simulation Engine

**Krishi-Twin** is a Digital Public Good (DPG) designed for smallholder farmers across India. Instead of providing static disease classifications, it executes dynamic, counterfactual decision simulations—comparing **Scenario A (Act Today)** vs. **Scenario B (Wait / Modify Action)**—to evaluate financial gain/loss in Indian Rupees (₹) alongside environmental wash-off risks[cite: 10].

The platform dynamically resolves GPS coordinates across all major Indian agricultural zones and streams localized voice advisories in regional languages (Tamil, Telugu, Kannada, Malayalam, Marathi, Hindi, English)[cite: 6, 8, 9, 10].

---

## 1. System Architecture Overview

```

[ S: Data Pipeline ] ──(POST Telemetry Payload)──> [ R: FastAPI / Gemini 3.6 Flash ]
(Pulls Live Weather & (Calculates Counterfactual
NDVI Satellite Data) ROI & Advisory Script)
│
▼
[ J: UI/UX & Voice Player ] <──(Streams MP3/JSON)─── [ Dynamic Audio Engine ]
(Renders Dual Cards & (Resolves GPS to Language:
Plays Audio in Dialect) ta, te, kn, ml, mr, hi, en)

```

---

## 2. Team Workflows & Responsibilities

- **R (Lead & Core AI Engine)**: Operates the FastAPI server (`main.py`), runs counterfactual simulations via Gemini 3.6 Flash, and hosts the dynamic Text-to-Speech (TTS) engine[cite: 8, 9].
- **S (Data Pipelines & Geospatial)**: Pulls satellite NDVI indices and live weather forecasts via Open-Meteo for any GPS coordinates in India, posting the payload to R's backend[cite: 5, 8].
- **J (UI/UX & Voice Interface)**: Renders the dual scenario cards (`Scenario A` vs. `Scenario B`) and streams localized MP3 advisories using `/api/v1/tts` or HTML5 audio elements[cite: 1, 9].

---

## 3. Directory Structure

```text
krishi-twin-backend/
├── main.py              # Primary FastAPI App (Endpoints: /api/v1/simulate & /api/v1/tts)
├── audioPipeline.py      # Location-aware Translation & GCP TTS Pipeline
├── weather_engine.py    # S's Live Weather Telemetry & Payload Generator
├── play_audio.py        # Local Audio Playback Test Script (using Pygame)
├── gcp-key.json         # GCP Service Account Credentials (TTS & Translation)
├── .env                 # API Keys & Port Configuration
└── README.md            # System Documentation

```

---

## 4. API Reference & Endpoints

### 1. Run Simulation Core

- **Endpoint**: `POST /api/v1/simulate`
- **Description**: Ingests field telemetry and generates a counterfactual ROI comparison using Gemini 3.6 Flash.

**Sample Request Payload (from S)**:

```json
{
  "engine": "Krishi-Twin-Decision-Core",
  "farm_profile": {
    "coordinates": { "latitude": 9.8821, "longitude": 78.0815 },
    "crop": "Rice (Paddy)",
    "farm_size_acres": 2.0,
    "detected_symptom": "Leaf Blight"
  },
  "geospatial_telemetry": {
    "mean_ndvi_index": 0.37,
    "canopy_vigor": "Stressed"
  },
  "meteorological_risk": {
    "rain_next_24h_mm": 18.5,
    "rain_probability_pct": 95,
    "max_wind_kmh": 24.6,
    "computed_washoff_risk": "HIGH"
  },
  "financial_inputs": {
    "spray_cost_inr": 850.0,
    "potential_crop_loss_inr": 4200.0
  }
}
```

---

### 2. Generate Multilingual Voice Advisory

- **Endpoint**: `POST /api/v1/tts`
- **Description**: Translates advisory text into the target regional language and returns a binary MP3 audio stream (`audio/mpeg`).

**Sample Request Payload (from J)**:

```json
{
  "text": "Do not spray medicine today because heavy rain will wash it away. Wait two days for clear weather.",
  "target_lang": "ta"
}
```

---

## 5. Regional Language & Geofencing Matrix

`audioPipeline.py` dynamically resolves farm coordinates or state selections to match regional voice profiles:

| Region / State                 | Primary Language | Language Code (`target_lang`) | GCP Voice Profile  |
| ------------------------------ | ---------------- | ----------------------------- | ------------------ |
| **Tamil Nadu**                 | Tamil            | `ta`                          | `ta-IN-Standard-A` |
| **Andhra Pradesh / Telangana** | Telugu           | `te`                          | `te-IN-Standard-A` |
| **Karnataka**                  | Kannada          | `kn`                          | `kn-IN-Standard-A` |
| **Kerala**                     | Malayalam        | `ml`                          | `ml-IN-Standard-A` |
| **Maharashtra**                | Marathi          | `mr`                          | `mr-IN-Standard-A` |
| **North / Central India**      | Hindi            | `hi`                          | `hi-IN-Neural2-A`  |
| **Pan-India**                  | Indian English   | `en`                          | `en-IN-Neural2-A`  |

---

## 6. How to Run & Verify the Pipeline

### 1. Start the Backend Server (R)

```powershell
python -m uvicorn main:app --reload --port 8080

```

Swagger UI will be available live at `http://localhost:8080/docs`.

### 2. Execute Live Simulation Pipeline (S)

```powershell
python weather_engine.py

```

### 3. Test Dynamic Audio & Speakers

```powershell
python play_audio.py

```

```

```

## 7. Final Readings
