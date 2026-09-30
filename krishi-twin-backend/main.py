import os
import json
import base64
import io

import torch
from PIL import Image
from torchvision import models, transforms
from torch import nn

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.cloud import translate
from google.cloud import texttospeech

from audioPipeline import resolve_language_from_coordinates
from weather_engine import build_dynamic_telemetry

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# SAMSAARI V2 RICE DISEASE MODEL
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "rice_disease_mobilenetv3_v2.pth"
)

DISEASE_CONFIDENCE_THRESHOLD = 0.70

MODEL_DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print(
    f"Loading Samsaari V2 disease model on "
    f"{MODEL_DEVICE}..."
)

checkpoint = torch.load(
    MODEL_PATH,
    map_location=MODEL_DEVICE
)

DISEASE_CLASSES = checkpoint["class_names"]

disease_model = models.mobilenet_v3_large(
    weights=None
)

num_features = (
    disease_model.classifier[-1].in_features
)

disease_model.classifier[-1] = nn.Linear(
    num_features,
    len(DISEASE_CLASSES)
)

disease_model.load_state_dict(
    checkpoint["model_state_dict"]
)

disease_model = disease_model.to(
    MODEL_DEVICE
)

disease_model.eval()

disease_transform = transforms.Compose([
    transforms.Resize((224, 224)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[
            0.485,
            0.456,
            0.406
        ],
        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])

print(
    "Samsaari V2 loaded successfully."
)

print(
    f"Classes: {DISEASE_CLASSES}"
)


# ============================================================
# GOOGLE CLOUD CREDENTIALS
# ============================================================

os.environ.setdefault(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        "gcp-key.json"
    )
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Krishi-Twin Decision Core",
    version="1.0.0",
    description="Counterfactual Agro-Financial Simulation Engine"
)


# ============================================================
# GOOGLE CLIENTS
# ============================================================

gemini_api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not gemini_api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set in the environment/.env file."
    )

ai_client = genai.Client(
    api_key=gemini_api_key
)

translate_client = (
    translate.TranslationServiceClient()
)

tts_client = (
    texttospeech.TextToSpeechClient()
)


# ============================================================
# GEMINI SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are the Krishi-Twin Counterfactual Financial Engine.

Analyze the provided farm payload.

Compare:
Scenario A = Spray/Act Today
Scenario B = Wait 48 hours / Defer Action

Use the provided weather, crop, market, financial and
disease information.

Output a JSON object with these exact keys:

- recommended_action:
  String. Must be exactly one of:
  'SPRAY', 'WAIT', or 'IRRIGATE'

- scenario_a_roi_inr:
  String. Calculate the net financial impact in INR.

- scenario_b_roi_inr:
  String. Calculate the net financial impact in INR.

- risk_factor:
  String. Explain the weather, wash-off, crop disease,
  or other relevant risk.

- voice_script_2_sentences:
  String. Exactly 2 simple sentences suitable for a
  low-literacy farmer.
"""


# ============================================================
# REGIONAL VOICES
# ============================================================

REGIONAL_VOICES = {

    "hi": {
        "language_code": "hi-IN",
        "name": "hi-IN-Neural2-A",
        "ssml_gender":
            texttospeech.SsmlVoiceGender.FEMALE
    },

    "te": {
        "language_code": "te-IN",
        "name": "te-IN-Standard-A",
        "ssml_gender":
            texttospeech.SsmlVoiceGender.FEMALE
    },

    "mr": {
        "language_code": "mr-IN",
        "name": "mr-IN-Standard-A",
        "ssml_gender":
            texttospeech.SsmlVoiceGender.FEMALE
    },

    "ta": {
        "language_code": "ta-IN",
        "name": "ta-IN-Standard-A",
        "ssml_gender":
            texttospeech.SsmlVoiceGender.FEMALE
    },

    "en": {
        "language_code": "en-IN",
        "name": "en-IN-Neural2-A",
        "ssml_gender":
            texttospeech.SsmlVoiceGender.FEMALE
    }
}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class KrishiTwinResponse(BaseModel):

    recommended_action: str
    scenario_a_roi_inr: str
    scenario_b_roi_inr: str
    risk_factor: str
    voice_script_2_sentences: str

    disease: str | None = None
    disease_confidence: float | None = None
    disease_uncertain: bool = False

    resolved_language: str | None = None
    translated_text: str | None = None
    audio_base64: str | None = None


class MultimodalSimulationRequest(BaseModel):

    engine: str | None = None

    timestamp: str | None = None

    farm_profile: dict

    geospatial_telemetry: dict = Field(
        default_factory=dict
    )

    meteorological_risk: dict = Field(
        default_factory=dict
    )

    market_telemetry: dict = Field(
        default_factory=dict
    )

    financial_inputs: dict = Field(
        default_factory=dict
    )

    image_base64: str | None = Field(
        default=None,
        description="Base64 string of crop leaf image"
    )


class MultilingualTTSRequest(BaseModel):

    text: str
    latitude: float
    longitude: float

# ============================================================
# MULTILINGUAL ADVISORY AUDIO
# ============================================================

def generate_advisory_audio(
    text: str,
    latitude: float,
    longitude: float
):
    target_lang = resolve_language_from_coordinates(
        latitude,
        longitude
    )

    print(
        f"Resolved language: {target_lang}",
        flush=True
    )

    translated_text = text

    if target_lang != "en":

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        if not project_id:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT is not set."
            )

        parent = (
            f"projects/{project_id}/locations/global"
        )

        translation_response = (
            translate_client.translate_text(
                request={
                    "parent": parent,
                    "contents": [text],
                    "mime_type": "text/plain",
                    "source_language_code": "en",
                    "target_language_code": target_lang
                }
            )
        )

        if translation_response.translations:
            translated_text = (
                translation_response
                .translations[0]
                .translated_text
            )

    voice_config = REGIONAL_VOICES.get(
        target_lang,
        REGIONAL_VOICES["en"]
    )

    synthesis_input = texttospeech.SynthesisInput(
        text=translated_text
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code=voice_config["language_code"],
        name=voice_config["name"],
        ssml_gender=voice_config["ssml_gender"]
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.90
    )

    tts_response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    audio_bytes = tts_response.audio_content

    print(
        f"Translated text: {translated_text}",
        flush=True
    )

    print(
        f"Audio generated: {len(audio_bytes)} bytes",
        flush=True
    )

    return {
        "resolved_language": target_lang,
        "translated_text": translated_text,
        "audio_base64": base64.b64encode(
            audio_bytes
        ).decode("utf-8")
    }
# ============================================================
# RICE DISEASE INFERENCE
# ============================================================

def predict_rice_disease(
    image_bytes: bytes
):

    image = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    image_tensor = disease_transform(
        image
    ).unsqueeze(0).to(
        MODEL_DEVICE
    )

    with torch.no_grad():

        outputs = disease_model(
            image_tensor
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        confidence, prediction = (
            probabilities.max(dim=1)
        )

    predicted_id = prediction.item()

    confidence_value = confidence.item()

    predicted_class = DISEASE_CLASSES[
        predicted_id
    ]

    uncertain = (
        confidence_value
        < DISEASE_CONFIDENCE_THRESHOLD
    )

    return {
        "disease": predicted_class,

        "confidence": round(
            confidence_value,
            4
        ),

        "uncertain": uncertain
    }

@app.post("/api/v1/disease-test")
async def disease_test(request: dict):
    try:
        image_base64 = request["image_base64"]
        image_bytes = base64.b64decode(image_base64)

        result = predict_rice_disease(image_bytes)

        return {
            "disease": result["disease"],
            "confidence": result["confidence"],
            "uncertain": result["uncertain"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ============================================================
# SIMULATION ENDPOINT
# ============================================================

@app.post(
    "/api/v1/simulate",
    response_model=KrishiTwinResponse
)
async def run_multimodal_simulation(
    payload: MultimodalSimulationRequest
):

    try:

        # --------------------------------------------------------
        # DYNAMIC TELEMETRY FROM PHONE GPS
        # --------------------------------------------------------

        coordinates = payload.farm_profile.get("coordinates", {})

        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")

        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=400,
                detail="farm_profile.coordinates.latitude and longitude are required."
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="farm_profile coordinates must be valid numbers."
            )

        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid latitude: {latitude}"
            )

        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid longitude: {longitude}"
            )

        crop = payload.farm_profile.get("crop", "Rice")
        acres = float(payload.farm_profile.get("farm_size_acres", 2.0))

        print(
            f"Production GPS: latitude={latitude}, longitude={longitude}",
            flush=True
        )

        dynamic = build_dynamic_telemetry(
            lat=latitude,
            lon=longitude,
            crop=crop,
            acres=acres,
        )

        # Backend-generated telemetry is authoritative.
        payload.geospatial_telemetry = dynamic["geospatial_telemetry"]
        payload.meteorological_risk = dynamic["meteorological_risk"]
        payload.market_telemetry = dynamic["market_telemetry"]
        payload.financial_inputs = dynamic["financial_inputs"]

        # Attach backend-resolved location to the farm profile.
        payload.farm_profile["location"] = dynamic["location"]

        print(
            "Dynamic telemetry generated successfully from phone GPS.",
            flush=True
        )

        # --------------------------------------------------------
        # Convert telemetry into JSON
        # --------------------------------------------------------

        telemetry_json = json.dumps(
            {
                "farm_profile":
                    payload.farm_profile,

                "geospatial_telemetry":
                    payload.geospatial_telemetry,

                "meteorological_risk":
                    payload.meteorological_risk,

                "market_telemetry":
                    payload.market_telemetry,

                "financial_inputs":
                    payload.financial_inputs
            },
            indent=2
        )

        contents = [
            f"Farm Telemetry Payload:\n{telemetry_json}"
        ]


        # --------------------------------------------------------
        # Default disease result
        # --------------------------------------------------------

        disease_result = {
            "disease": None,
            "confidence": None,
            "uncertain": False
        }


        # --------------------------------------------------------
        # Process image
        # --------------------------------------------------------

        if payload.image_base64:

            try:

                image_bytes = base64.b64decode(
                    payload.image_base64
                )

                # ------------------------------------------------
                # V2 DISEASE PREDICTION
                # ------------------------------------------------

                disease_result = (
                    predict_rice_disease(
                        image_bytes
                    )
                )

                print(
                    "\nSamsaari V2 Prediction:"
                )

                print(
                    f"  Disease: "
                    f"{disease_result['disease']}"
                )

                print(
                    f"  Confidence: "
                    f"{disease_result['confidence']:.2%}"
                )

                print(
                    f"  Uncertain: "
                    f"{disease_result['uncertain']}"
                )


                # ------------------------------------------------
                # Send V2 result to Gemini
                # ------------------------------------------------

                contents.append(
                    f"""
Samsaari V2 Rice Disease Detection:

{json.dumps(
    disease_result,
    indent=2
)}

IMPORTANT:
- This disease prediction comes from the
  dedicated Samsaari V2 rice disease classifier.
- The classifier uses a 70% confidence threshold.
- If "uncertain" is true, do not treat the disease
  prediction as definitive.
- Consider the disease result and uncertainty when
  generating the recommendation.
"""
                )


                # ------------------------------------------------
                # Keep image available to Gemini
                # ------------------------------------------------

                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    )
                )


            except Exception as image_error:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid image_base64: "
                        f"{image_error}"
                    )
                )


        # --------------------------------------------------------
        # Gemini request
        # --------------------------------------------------------

        response = (
            ai_client.models.generate_content(
                model="gemini-3.5-flash-lite",

                contents=contents,

                config=types.GenerateContentConfig(
                    system_instruction=
                        SYSTEM_INSTRUCTION,

                    response_mime_type=
                        "application/json",

                    response_schema=
                        KrishiTwinResponse,

                    temperature=0.2
                )
            )
        )


        # --------------------------------------------------------
        # Validate Gemini response
        # --------------------------------------------------------

        if not response.text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        result = (
            KrishiTwinResponse
            .model_validate_json(
                response.text
            )
        )

        # SAFETY OVERRIDE
        if disease_result["uncertain"]:
            result.recommended_action = "WAIT"

            result.risk_factor = (
                f"Disease prediction confidence is below the 70% threshold "
                f"at {disease_result['confidence']:.1%}. "
                "The result is uncertain, so a clearer crop image is needed "
                "before taking disease-specific action."
            )

            result.voice_script_2_sentences = (
                "Do not spray your rice crop yet because the disease result is uncertain. "
                "Please take a clearer photo of the affected leaf and check again."
            )

        result.disease = disease_result["disease"]
        result.disease_confidence = disease_result["confidence"]
        result.disease_uncertain = disease_result["uncertain"]

        # --------------------------------------------------------
        # Attach V2 disease result
        # --------------------------------------------------------

        result.disease = (
            disease_result["disease"]
        )

        result.disease_confidence = (
            disease_result["confidence"]
        )

        result.disease_uncertain = (
            disease_result["uncertain"]
        )


        # --------------------------------------------------------
        # Generate multilingual advisory audio
        # --------------------------------------------------------

        coordinates = payload.farm_profile.get(
            "coordinates",
            {}
        )

        latitude = coordinates.get("latitude")
        longitude = coordinates.get("longitude")

        if latitude is not None and longitude is not None:

            audio_result = generate_advisory_audio(
                text=result.voice_script_2_sentences,
                latitude=latitude,
                longitude=longitude
            )

            result.resolved_language = (
                audio_result["resolved_language"]
            )

            result.translated_text = (
                audio_result["translated_text"]
            )

            result.audio_base64 = (
                audio_result["audio_base64"]
            )

        return result


    except HTTPException:

        raise


    except Exception as e:

        print(
            f"Backend Error: "
            f"{type(e).__name__}: "
            f"{str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

# ============================================================
# TEXT TO SPEECH ENDPOINT
# ============================================================

# ============================================================
# MULTILINGUAL TTS
# ============================================================

from audioPipeline import resolve_language_from_coordinates
from weather_engine import build_dynamic_telemetry


class MultilingualTTSRequest(BaseModel):
    text: str
    latitude: float
    longitude: float


@app.post("/api/v1/tts")
async def generate_multilingual_tts(
    payload: MultilingualTTSRequest
):
    try:
        print("\n--- MULTILINGUAL TTS ---", flush=True)
        print(f"Text: {payload.text}", flush=True)
        print(
            f"Coordinates: {payload.latitude}, {payload.longitude}",
            flush=True
        )

        # --------------------------------------------------------
        # Resolve language from farm coordinates
        # --------------------------------------------------------
        target_lang = resolve_language_from_coordinates(
            payload.latitude,
            payload.longitude
        )

        print(
            f"Resolved language: {target_lang}",
            flush=True
        )

        # --------------------------------------------------------
        # Translation
        # --------------------------------------------------------
        translated_text = payload.text

        if target_lang != "en":

            project_id = os.getenv(
                "GOOGLE_CLOUD_PROJECT"
            )

            if not project_id:
                raise ValueError(
                    "GOOGLE_CLOUD_PROJECT is not set."
                )

            parent = (
                f"projects/{project_id}/locations/global"
            )

            translation_response = (
                translate_client.translate_text(
                    request={
                        "parent": parent,
                        "contents": [
                            payload.text
                        ],
                        "mime_type": "text/plain",
                        "source_language_code": "en",
                        "target_language_code": target_lang
                    }
                )
            )

            if translation_response.translations:
                translated_text = (
                    translation_response
                    .translations[0]
                    .translated_text
                )

        # --------------------------------------------------------
        # Select regional voice
        # --------------------------------------------------------
        voice_config = REGIONAL_VOICES.get(
            target_lang,
            REGIONAL_VOICES["en"]
        )

        # --------------------------------------------------------
        # Create TTS input
        # --------------------------------------------------------
        synthesis_input = (
            texttospeech.SynthesisInput(
                text=translated_text
            )
        )

        # --------------------------------------------------------
        # Voice configuration
        # --------------------------------------------------------
        voice = (
            texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"],
                ssml_gender=voice_config["ssml_gender"]
            )
        )

        # --------------------------------------------------------
        # Audio configuration
        # --------------------------------------------------------
        audio_config = (
            texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.90
            )
        )

        # --------------------------------------------------------
        # Generate speech
        # --------------------------------------------------------
        tts_response = (
            tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
        )

        audio_bytes = tts_response.audio_content

        print(
            f"Translated text: {translated_text}",
            flush=True
        )

        print(
            f"Audio generated: {len(audio_bytes)} bytes",
            flush=True
        )

        # --------------------------------------------------------
        # Return MP3 + metadata
        # --------------------------------------------------------
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                
                "X-Resolved-Language": target_lang,
                "Content-Disposition":
                    "inline; filename=advisory.mp3"
            }
        )

    except Exception as e:

        print(
            "\n--- BACKEND TTS CRASH ---",
            flush=True
        )

        print(
            f"{type(e).__name__}: {str(e)}",
            flush=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# LOCAL SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                8080
            )
        )
    )
