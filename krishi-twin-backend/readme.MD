# Krishi-Twin: Counterfactual Agro-Financial Simulation Engine

**Krishi-Twin** is an AI-powered agricultural decision-support platform designed to help smallholder farmers across India make informed crop-treatment decisions. Rather than providing only static disease classifications, it simulates alternative courses of action by comparing **Scenario A (Act Today)** against **Scenario B (Wait / Modify Action)** to estimate financial outcomes in Indian Rupees (₹) and assess environmental risks such as pesticide wash-off.

The platform combines geospatial information, weather forecasts, agricultural telemetry, and AI-generated recommendations to provide contextual decision support. It also supports multilingual voice advisories in Tamil, Telugu, Kannada, Malayalam, Marathi, Hindi, and English.

---

## 1. System Architecture

```text
┌──────────────────────────────┐
│ S: Data Pipeline             │
│                              │
│ Live Weather & Satellite     │
│ NDVI Data                    │
└──────────────┬───────────────┘
               │
               │ POST Telemetry Payload
               ▼
┌──────────────────────────────┐
│ R: FastAPI Backend           │
│                              │
│ Counterfactual Simulation    │
│ Gemini-Powered Reasoning     │
│ Financial ROI Estimation     │
└──────────────┬───────────────┘
               │
               │ Simulation Results
               ▼
┌──────────────────────────────┐
│ J: UI/UX & Voice Interface   │
│                              │
│ Scenario A vs. Scenario B    │
│ Contextual Recommendations   │
│ Multilingual Audio Playback  │
└──────────────┬───────────────┘
               │
               │ Audio Request
               ▼
┌──────────────────────────────┐
│ Dynamic Audio Engine         │
│                              │
│ Language Resolution          │
│ Translation & Text-to-Speech │
└──────────────────────────────┘
```

### Decision Workflow

1. **Collect field telemetry:** Gather farm coordinates, crop information, disease symptoms, weather forecasts, and available vegetation indices.
2. **Evaluate alternatives:** Compare acting immediately against waiting or modifying the treatment plan.
3. **Estimate financial outcomes:** Evaluate treatment costs and potential crop losses to estimate the relative financial impact of each scenario.
4. **Generate recommendations:** Use AI-powered reasoning to produce contextual advisories.
5. **Deliver localized guidance:** Present the results through the application and provide voice advisories in the selected regional language.

---

## 2. Team Workflows & Responsibilities

- **R — Lead & Core AI Engine and UI/UX:** Develops and operates the FastAPI backend in `main.py`, coordinates counterfactual simulations using Gemini, and integrates the text-to-speech pipeline.
- **S — Data Pipelines & Geospatial:** Handles weather telemetry using Open-Meteo and satellite NDVI data, preparing farm-specific payloads for the backend.
- **J — Voice Interface:** Develops the interface for comparing Scenario A and Scenario B and integrates multilingual audio playback through `/api/v1/tts` or HTML5 audio elements.

---

## 3. Project Structure

```text
krishi-twin-backend/
├── main.py              # FastAPI application and API endpoints
├── audioPipeline.py     # Translation and Google Cloud TTS pipeline
├── weather_engine.py    # Weather telemetry and payload generation
├── play_audio.py        # Local audio playback testing
├── gcp-key.json         # Google Cloud service account credentials
├── .env                 # API keys and configuration
└── README.md            # Project documentation
```

**Security note:** Never commit `gcp-key.json`, `.env`, or other credentials to version control. Add them to `.gitignore` and use environment variables or a secrets manager for deployment.

---

## 4. API Reference

### 4.1 Run a Counterfactual Simulation

**Endpoint:** `POST /api/v1/simulate`

**Description:** Accepts farm telemetry and financial inputs to generate a counterfactual comparison of potential agricultural treatment decisions.

**Example request:**

```json
{
  "engine": "Krishi-Twin-Decision-Core",
  "farm_profile": {
    "coordinates": {
      "latitude": 9.8821,
      "longitude": 78.0815
    },
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

The payload above is an illustrative example of the telemetry and financial inputs supplied to the simulation engine.

### 4.2 Generate a Multilingual Voice Advisory

**Endpoint:** `POST /api/v1/tts`

**Description:** Accepts advisory text and a target language code, then returns an MP3 audio stream with the media type `audio/mpeg`.

**Example request:**

```json
{
  "text": "Do not spray medicine today because heavy rain will wash it away. Wait two days for clear weather.",
  "target_lang": "ta"
}
```

The example requests a Tamil-language advisory.

---

## 5. Regional Language Support

The audio pipeline supports language selection based on farm location or an explicitly selected state or language.

| Region | Language | Code |
|---|---|---|
| Tamil Nadu | Tamil | `ta` |
| Andhra Pradesh / Telangana | Telugu | `te` |
| Karnataka | Kannada | `kn` |
| Kerala | Malayalam | `ml` |
| Maharashtra | Marathi | `mr` |
| North / Central India | Hindi | `hi` |
| Pan-India | Indian English | `en` |

The configured Google Cloud Text-to-Speech voice profiles are:

| Language | Voice Profile |
|---|---|
| Tamil | `ta-IN-Standard-A` |
| Telugu | `te-IN-Standard-A` |
| Kannada | `kn-IN-Standard-A` |
| Malayalam | `ml-IN-Standard-A` |
| Marathi | `mr-IN-Standard-A` |
| Hindi | `hi-IN-Neural2-A` |
| Indian English | `en-IN-Neural2-A` |

---

## 6. Technology Stack

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| AI reasoning | Gemini API |
| Weather data | Open-Meteo |
| Satellite telemetry | NDVI data source |
| Translation and voice | Google Cloud Translation / Text-to-Speech |
| API communication | REST, JSON |
| Audio playback | MP3, HTML5 Audio |
| Development | Python, PowerShell |

*Note: Verify the exact Gemini model identifier, satellite data provider, and Google Cloud services configured in your implementation before deployment.*

---

## 7. Setup & Execution

### Prerequisites

Install or configure the following:

- Python 3.10 or later, compatible with your dependencies
- Required Python packages
- Gemini API credentials
- Google Cloud credentials if translation or text-to-speech is enabled
- Access to the configured weather and satellite data sources

### Step 1: Navigate to the Backend

Open PowerShell in the backend directory:

```powershell
cd krishi-twin-backend
```

### Step 2: Configure Environment Variables

Create a `.env` file containing the credentials required by your implementation.

For example:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Add any additional variables required by `main.py`, `weather_engine.py`, and `audioPipeline.py`.

Do not commit real API keys or service account credentials to GitHub.

### Step 3: Install Dependencies

If the project includes a `requirements.txt` file, run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If no dependency file exists, create one containing the actual dependencies used by the project before following this step.

### Step 4: Start the Backend

```powershell
python -m uvicorn main:app --reload --port 8080
```

The local API should be available at:

- **API base URL:** `http://localhost:8080`
- **Swagger documentation:** `http://localhost:8080/docs`

These URLs assume the server starts successfully on port `8080`.

### Step 5: Run the Weather Pipeline

Open another PowerShell terminal in the project directory and run:

```powershell
python weather_engine.py
```

This runs the weather telemetry and payload-generation script.

### Step 6: Test Audio Playback

```powershell
python play_audio.py
```

This runs the local audio playback test script.

---

## 8. Example Decision Scenario

Consider a farmer deciding whether to spray a crop treatment before forecast rainfall.

**Farm conditions**

- Crop: Rice
- Farm size: 2 acres
- Detected symptom: Leaf blight
- Forecast rainfall: 18.5 mm over the next 24 hours
- Estimated spray cost: ₹850
- Potential crop loss: ₹4,200

### Scenario A — Act Today

Evaluate the financial implications of applying the treatment immediately, considering its cost and the forecast wash-off risk.

### Scenario B — Wait or Modify Action

Evaluate the alternative of delaying or modifying treatment based on the forecast conditions and potential crop-loss implications.

### Expected outcome

The simulation compares the two scenarios and presents estimated financial outcomes and contextual recommendations to support the farmer's decision.

*The values above are illustrative inputs, not verified predictions or guaranteed financial savings. Actual recommendations depend on the model output, weather conditions, crop status, and treatment-specific guidance.*

---

## 9. Limitations & Future Improvements

### Current considerations

- AI-generated recommendations may be inaccurate or incomplete and should be validated against agricultural guidance.
- Satellite NDVI measurements can be affected by resolution, cloud cover, and data availability.
- Weather forecasts are estimates and may change.
- Financial outcomes depend on assumptions about treatment effectiveness, crop losses, and market prices.
- Translation and speech quality may vary across languages.
- API availability and rate limits can affect the service.

### Potential improvements

- Add persistent storage for farm profiles, simulations, and historical decisions.
- Incorporate validated crop-specific treatment recommendations.
- Add confidence intervals and sensitivity analysis for financial estimates.
- Improve satellite-data coverage and temporal vegetation tracking.
- Add offline support for areas with limited connectivity.
- Expand regional language support and evaluate speech quality with native speakers.
- Track recommendation outcomes to assess real-world usefulness.

---

## 10. Project Goal

Krishi-Twin aims to move agricultural decision support beyond static classification by combining AI reasoning, environmental context, and financial scenario analysis.

By comparing alternative actions and communicating recommendations in regional languages, the platform seeks to help smallholder farmers make more informed and context-aware decisions.
