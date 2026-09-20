import json
from google import genai
from google.genai import types

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

# 2. Define the 3 Baseline Scenarios
scenarios = [
    {
        "scenario_name": "Case 1: Heavy Rain Wash-off Risk",
        "farm_profile": {"crop": "Rice (Paddy)", "detected_symptom": "Leaf Folder Pest"},
        "geospatial_telemetry": {"mean_ndvi_index": 0.65, "canopy_vigor": "Healthy"},
        "meteorological_risk": {"rain_next_24h_mm": 18.5, "rain_probability_pct": 95, "computed_washoff_risk": "HIGH"},
        "financial_inputs": {"spray_cost_inr": 800.0, "potential_crop_loss_inr": 3500.0}
    },
    {
        "scenario_name": "Case 2: Optimal Spray Window",
        "farm_profile": {"crop": "Rice (Paddy)", "detected_symptom": "Leaf Blight"},
        "geospatial_telemetry": {"mean_ndvi_index": 0.45, "canopy_vigor": "Moderate"},
        "meteorological_risk": {"rain_next_24h_mm": 0.0, "rain_probability_pct": 10, "computed_washoff_risk": "LOW"},
        "financial_inputs": {"spray_cost_inr": 850.0, "potential_crop_loss_inr": 4200.0}
    },
    {
        "scenario_name": "Case 3: False Alarm (Drought Stress)",
        "farm_profile": {"crop": "Cotton", "detected_symptom": "Yellowing Leaves (Suspected Disease)"},
        "geospatial_telemetry": {"mean_ndvi_index": 0.25, "canopy_vigor": "Severe Stress"},
        "meteorological_risk": {"rain_next_24h_mm": 0.0, "rain_probability_pct": 0, "max_temperature_c": 39.5, "computed_washoff_risk": "LOW"},
        "financial_inputs": {"spray_cost_inr": 1200.0, "potential_crop_loss_inr": 6000.0}
    }
]

system_instruction = """
You are the Krishi-Twin Counterfactual Financial Engine. 
Analyze the provided JSON payload. 
Compare Scenario A (Spray Today) vs Scenario B (Wait/Pivot).
Output a JSON object with these exact keys:
- 'recommended_action' (String: 'SPRAY', 'WAIT', or 'IRRIGATE')
- 'scenario_a_roi_inr' (String)
- 'scenario_b_roi_inr' (String)
- 'risk_factor' (String)
- 'voice_script_2_sentences' (String)
"""

# 3. Run the Automated Test Loop
print("Initializing Krishi-Twin Automated Scenario Runner...\n" + "="*50)

for case in scenarios:
    print(f"\nRunning {case['scenario_name']}...")
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=json.dumps(case),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=system_instruction
        )
    )
    
    # Parse and print the AI's JSON response cleanly
    result = json.loads(response.text)
    print(f"Action: {result['recommended_action']}")
    print(f"Scenario A (Act) ROI: ₹{result['scenario_a_roi_inr']}")
    print(f"Scenario B (Wait) ROI: ₹{result['scenario_b_roi_inr']}")
    print(f"Advisory: {result['voice_script_2_sentences']}")
    print("-" * 50)