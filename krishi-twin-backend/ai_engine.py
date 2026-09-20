from google import genai
from google.genai import types
import json

# 1. Initialize the AI Client
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the hidden key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize the AI Client safely
client = genai.Client(api_key=api_key)

# 2. The Payload (Pasted exactly from your previous output)
farm_data = {
  "engine": "Krishi-Twin-Decision-Core",
  "timestamp": "2026-08-23T16:28:32.928285Z",
  "farm_profile": {
    "coordinates": {"latitude": 9.8821, "longitude": 78.0815},
    "crop": "Rice (Paddy)",
    "farm_size_acres": 2.0,
    "detected_symptom": "Leaf Blight"
  },
  "geospatial_telemetry": {
    "mean_ndvi_index": 0.37,
    "canopy_vigor": "Stressed"
  },
  "meteorological_risk": {
    "rain_next_24h_mm": 0.7,
    "rain_probability_pct": 69,
    "max_wind_kmh": 24.6,
    "computed_washoff_risk": "LOW"
  },
  "financial_inputs": {
    "spray_cost_inr": 850.0,
    "potential_crop_loss_inr": 4200.0
  }
}

# 3. Instruct the AI to act as the Risk Engine
system_instruction = """
You are the Krishi-Twin Counterfactual Financial Engine. 
Analyze the provided JSON payload. 
Compare Scenario A (Spray Today) vs Scenario B (Wait 48 hours).
Output a JSON object with these exact keys:
- 'recommended_action' (String: 'SPRAY' or 'WAIT')
- 'scenario_a_roi_inr' (String: Calculate the net financial impact)
- 'scenario_b_roi_inr' (String: Calculate the net financial impact)
- 'risk_factor' (String: Explanation of the weather/disease risk)
- 'voice_script_2_sentences' (String: A simple, 2-sentence advisory for a low-literacy farmer)
"""

# 4. Generate the Decision
print("Running Krishi-Twin Simulation...")
response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=json.dumps(farm_data),
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        system_instruction=system_instruction
    )
)

# 5. Output the final AI decision
print("\n--- Final Krishi-Twin Output ---")
print(response.text)