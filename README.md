# Samsaari 🌾
### AI-Powered Decision Support for Rice Farmers

Samsaari is a farmer-focused Android application that combines AI-based rice disease detection, weather information, market data, and financial analysis to help farmers make more informed crop-management decisions.

Instead of only identifying a disease, Samsaari compares two possible scenarios — **Act Today** and **Wait** — and provides a contextual recommendation with multilingual text and voice guidance.

---

## ✨ Key Features

* **🌱 Rice Disease Detection**
  * MobileNetV3-Large based image classifier
  * Supports 10 rice disease/health classes
  * Confidence-based uncertainty handling (70% confidence threshold)

* **📍 Location-Aware Analysis**
  * Uses the device's GPS coordinates
  * Provides location-relevant agricultural context

* **🌦️ Weather Intelligence**
  * Rainfall probability
  * Expected rainfall
  * Wind speed
  * Wash-off risk
  * Powered by Open-Meteo

* **📊 Market & Financial Analysis**
  * Rice market information
  * Scenario-based financial comparison
  * ROI estimation for different decisions

* **🤖 AI Decision Core**
  * Gemini-based reasoning
  * Combines disease, weather, market, and financial information
  * Generates an actionable recommendation

* **🗣️ Multilingual Voice Advisory**
  * Regional-language translation
  * Text-to-speech output
  * Designed for accessible farmer communication

---

## 🔄 How It Works

```
Rice Leaf Image
      ↓
AI Disease Detection
      ↓
GPS Location
      ↓
Weather + Market + Financial Data
      ↓
Gemini Decision Core
      ↓
┌───────────────────┐
│   Act Today       │
│        vs         │
│      Wait         │
└───────────────────┘
      ↓
Risk + ROI + Recommendation
      ↓
Translated Text + Voice Advisory
```

---

## 🧠 Disease Detection

Samsaari uses a **MobileNetV3-Large** model trained for rice disease classification.

### Supported Classes
* Bacterial Leaf Blight
* Bacterial Leaf Streak
* Bacterial Panicle Blight
* Blast
* Brown Spot
* Dead Heart
* Downy Mildew
* Hispa
* Normal
* Tungro

> **Note:** Predictions below the 70% confidence threshold are treated as uncertain rather than being presented as a confident diagnosis.

---

## 📱 Application Flow

```
Home
 ↓
Camera / Gallery
 ↓
Crop Image
 ↓
Analysis
 ↓
Disease + Confidence
 ↓
Decision Comparison
 ↓
Recommendation
 ↓
Voice Advisory
```

---

## 🏗️ Architecture

* **Android Application**
  * Kotlin
  * Jetpack Compose
  * CameraX
  * OkHttp
  * Android Location APIs

* **Backend**
  * Python
  * FastAPI
  * REST API

* **AI**
  * PyTorch
  * MobileNetV3-Large
  * Gemini

* **External Data Services**
  * Open-Meteo
  * Farmer.in Market API
  * OpenStreetMap Nominatim

* **Language & Voice**
  * Translation service
  * Google Cloud Text-to-Speech

---

## 📈 Model Performance

### Validation
| Metric | Result |
| :--- | :--- |
| Validation Accuracy | 97.06% |
| Macro F1 | 0.9626 |

### External Evaluation
| Metric | Result |
| :--- | :--- |
| Images Evaluated | 150 |
| Accuracy | 98.67% |
| Macro F1 | 0.9899 |
| Average Confidence | 79.79% |
| Below 70% Confidence | 26 / 150 |

*These results represent the current evaluation of the disease-classification model and should not be interpreted as overall field performance.*

---

## 🛠️ Project Structure

```
Samsaari/
│
├── app/
│   └── src/
│       └── main/
│           ├── java/
│           ├── res/
│           └── AndroidManifest.xml
│
├── backend/
│   ├── main.py
│   ├── weather_engine.py
│   ├── audioPipeline.py
│   ├── requirements.txt
│   └── rice_disease_mobilenetv3_v2.pth
│
├── README.md
└── ...
```

---

## 🚀 Running the Application

### Backend
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
   ```
   The main API endpoint is: `POST /api/v1/simulate`

### Android
1. Open the Android project and build the application using Gradle.
2. The Android application communicates with the deployed Samsaari backend through the `/api/v1/simulate` endpoint.

---

## 🔐 API Configuration

* The backend requires the appropriate API credentials/environment variables for services used by the application, including the Gemini and Google Cloud services.
* **Do not** commit API keys, credentials, or other secrets to the repository.
* Use environment variables for sensitive configuration.

---

## 📊 Decision Output

The backend returns information including:
* Disease
* Disease confidence
* Uncertainty status
* Recommended action
* Scenario A ROI
* Scenario B ROI
* Risk factor
* Farmer advisory
* Resolved language
* Translated advisory
* Audio advisory

---

## 🎯 Objective

Samsaari aims to bridge the gap between AI-based crop diagnosis and practical agricultural decision-making by bringing multiple sources of farm information into a single, accessible workflow.

> **Detect the problem. Understand the context. Compare the choices. Make an informed decision.**

---

## 🔮 Future Scope

* Larger real-world agricultural image datasets
* Additional crops and diseases
* More regional languages
* Offline/low-connectivity support
* Farm history and personalization
* Additional remote-sensing information
* Expanded agricultural data integrations

---

## 👥 Project

**Samsaari — AI-Powered Agricultural Decision Support**  
Built as an AI/ML agricultural technology prototype focused on rice farming and farmer-centric decision support.
