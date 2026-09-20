import os
import json
import base64

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.cloud import translate
from google.cloud import texttospeech


load_dotenv()

os.environ.setdefault(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "gcp-key.json")
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

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set in the environment/.env file."
    )

ai_client = genai.Client(api_key=gemini_api_key)

translate_client = translate.TranslationServiceClient()
tts_client = texttospeech.TextToSpeechClient()


# ============================================================
# GEMINI SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are the Krishi-Twin Counterfactual Financial Engine.

Analyze the provided farm payload.

Compare:
Scenario A = Spray/Act Today
Scenario B = Wait 48 hours / Defer Action

Use the provided weather, crop, market, NDVI, financial and disease information.

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
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "te": {
        "language_code": "te-IN",
        "name": "te-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "mr": {
        "language_code": "mr-IN",
        "name": "mr-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "ta": {
        "language_code": "ta-IN",
        "name": "ta-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },
    "en": {
        "language_code": "en-IN",
        "name": "en-IN-Neural2-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
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


class MultimodalSimulationRequest(BaseModel):
    engine: str | None = None
    timestamp: str | None = None

    farm_profile: dict
    geospatial_telemetry: dict
    meteorological_risk: dict

    market_telemetry: dict = Field(default_factory=dict)

    financial_inputs: dict

    image_base64: str | None = Field(
        default=None,
        description="Base64 string of crop leaf image"
    )


class MultilingualTTSRequest(BaseModel):
    text: str
    target_lang: str = "en"


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
        # Convert telemetry into JSON
        # --------------------------------------------------------

        telemetry_json = json.dumps(
            {
                "farm_profile": payload.farm_profile,
                "geospatial_telemetry": payload.geospatial_telemetry,
                "meteorological_risk": payload.meteorological_risk,
                "market_telemetry": payload.market_telemetry,
                "financial_inputs": payload.financial_inputs
            },
            indent=2
        )

        contents = [
            f"Farm Telemetry Payload:\n{telemetry_json}"
        ]


        # --------------------------------------------------------
        # Add image if supplied
        # --------------------------------------------------------

        if payload.image_base64:

            try:
                image_bytes = base64.b64decode(
                    payload.image_base64
                )

                contents.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/jpeg"
                    )
                )

            except Exception as image_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image_base64: {image_error}"
                )


        # --------------------------------------------------------
        # Gemini request
        # --------------------------------------------------------

        response = ai_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=KrishiTwinResponse,
                temperature=0.2
            )
        )


        # --------------------------------------------------------
        # Validate Gemini response
        # --------------------------------------------------------

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        result = KrishiTwinResponse.model_validate_json(
            response.text
        )

        return result


    except HTTPException:
        raise

    except Exception as e:

        print(
            f"Backend Error: {type(e).__name__}: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# TEXT TO SPEECH ENDPOINT
# ============================================================

@app.post("/api/v1/tts")
async def generate_multilingual_tts(
    payload: MultilingualTTSRequest
):

    try:

        translated_text = payload.text

        # --------------------------------------------------------
        # Translation
        # --------------------------------------------------------

        if payload.target_lang != "en":

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
                        "contents": [payload.text],
                        "mime_type": "text/plain",
                        "source_language_code": "en",
                        "target_language_code": payload.target_lang
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
            payload.target_lang,
            REGIONAL_VOICES["en"]
        )


        # --------------------------------------------------------
        # Create TTS input
        # --------------------------------------------------------

        synthesis_input = texttospeech.SynthesisInput(
            text=translated_text
        )


        # --------------------------------------------------------
        # Voice configuration
        # --------------------------------------------------------

        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["language_code"],
            name=voice_config["name"],
            ssml_gender=voice_config["ssml_gender"]
        )


        # --------------------------------------------------------
        # Audio configuration
        # --------------------------------------------------------

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.90
        )


        # --------------------------------------------------------
        # Generate speech
        # --------------------------------------------------------

        tts_response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )


        return Response(
            content=tts_response.audio_content,
            media_type="audio/mpeg"
        )


    except Exception as e:

        print(
            f"\n--- BACKEND TTS CRASH ---\n"
            f"{type(e).__name__}: {str(e)}\n"
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
        port=int(os.getenv("PORT", 8080))
    )