import os
from functools import lru_cache

import requests
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech


os.environ.setdefault(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "gcp-key.json"
)


# ============================================================
# REGIONAL VOICE CONFIGURATION
# ============================================================

REGIONAL_VOICES = {
    "ta": {
        "language_code": "ta-IN",
        "name": "ta-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },

    "te": {
        "language_code": "te-IN",
        "name": "te-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },

    "kn": {
        "language_code": "kn-IN",
        "name": "kn-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },

    "ml": {
        "language_code": "ml-IN",
        "name": "ml-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },

    "mr": {
        "language_code": "mr-IN",
        "name": "mr-IN-Standard-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },

    "hi": {
        "language_code": "hi-IN",
        "name": "hi-IN-Neural2-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    },

    "en": {
        "language_code": "en-IN",
        "name": "en-IN-Neural2-A",
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    }
}


# ============================================================
# STATE → LANGUAGE MAPPING
# ============================================================

STATE_LANGUAGE_MAP = {

    # Tamil
    "Tamil Nadu": "ta",

    # Telugu
    "Andhra Pradesh": "te",
    "Telangana": "te",

    # Kannada
    "Karnataka": "kn",

    # Malayalam
    "Kerala": "ml",

    # Marathi
    "Maharashtra": "mr",

    # Hindi
    #
    # States where Hindi is used as the primary/default
    # agricultural advisory language in this backend.
    "Uttar Pradesh": "hi",
    "Madhya Pradesh": "hi",
    "Rajasthan": "hi",
    "Bihar": "hi",
    "Jharkhand": "hi",
    "Chhattisgarh": "hi",
    "Haryana": "hi",
    "Punjab": "hi",
    "Uttarakhand": "hi",
    "Himachal Pradesh": "hi",
    "Delhi": "hi",
    "Jammu and Kashmir": "hi",
    "Ladakh": "hi"
}


# ============================================================
# CLIENTS
# ============================================================

translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient()


# ============================================================
# REVERSE GEOCODING
# ============================================================

GOOGLE_GEOCODING_URL = (
    "https://maps.googleapis.com/maps/api/geocode/json"
)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


@lru_cache(maxsize=512)
def _reverse_geocode_state(
    latitude_rounded: float,
    longitude_rounded: float
) -> str | None:

    if not GOOGLE_MAPS_API_KEY:
        print(
            "WARNING: GOOGLE_MAPS_API_KEY not configured. "
            "Using Hindi fallback."
        )
        return None

    params = {
        "latlng": f"{latitude_rounded},{longitude_rounded}",
        "key": GOOGLE_MAPS_API_KEY,
        "language": "en"
    }

    try:
        response = requests.get(
            GOOGLE_GEOCODING_URL,
            params=params,
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "OK":
            print(
                f"Reverse geocoding failed: "
                f"{data.get('status')}"
            )
            return None

        for result in data.get("results", []):

            for component in result.get(
                "address_components",
                []
            ):

                if "administrative_area_level_1" in component.get(
                    "types",
                    []
                ):
                    return component.get("long_name")

    except requests.RequestException as exc:
        print(
            f"Reverse geocoding request failed: {exc}"
        )

    return None


# ============================================================
# LANGUAGE RESOLUTION
# ============================================================

def resolve_language_from_coordinates(
    lat: float,
    lon: float
) -> str:
    """
    Resolve the regional advisory language from GPS coordinates.

    Uses administrative state boundaries through reverse geocoding
    rather than overlapping latitude/longitude bounding boxes.
    """

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return "hi"

    if not (-90 <= lat <= 90):
        return "hi"

    if not (-180 <= lon <= 180):
        return "hi"

    # Round coordinates so nearby requests can share the cache.
    rounded_lat = round(lat, 4)
    rounded_lon = round(lon, 4)

    state = _reverse_geocode_state(
        rounded_lat,
        rounded_lon
    )

    if not state:
        return "hi"

    language = STATE_LANGUAGE_MAP.get(
        state,
        "hi"
    )

    print(
        f"Regional geofence: "
        f"({lat}, {lon}) -> {state} -> {language}"
    )

    return language


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _validate_text(raw_text: str) -> str:

    if raw_text is None:
        raise ValueError("raw_text cannot be None")

    if not isinstance(raw_text, str):
        raw_text = str(raw_text)

    raw_text = raw_text.strip()

    if not raw_text:
        raise ValueError("raw_text cannot be empty")

    return raw_text


# ============================================================
# AUDIO PIPELINE
# ============================================================

def process_advisory_audio_by_coordinates(
    raw_text: str,
    lat: float,
    lon: float
) -> dict:
    """
    Translate and synthesize an agricultural advisory.

    Returns raw MP3 bytes without decoding/re-encoding them.
    """

    raw_text = _validate_text(raw_text)

    target_lang = resolve_language_from_coordinates(
        lat,
        lon
    )

    translated_text = raw_text

    # --------------------------------------------------------
    # TRANSLATION
    # --------------------------------------------------------

    if target_lang != "en":

        result = translate_client.translate(
            raw_text,
            target_language=target_lang,
            source_language="en"
        )

        translated_text = result.get(
            "translatedText",
            raw_text
        )

        if not isinstance(translated_text, str):
            translated_text = str(translated_text)

    # --------------------------------------------------------
    # VOICE SELECTION
    # --------------------------------------------------------

    voice_config = REGIONAL_VOICES.get(
        target_lang,
        REGIONAL_VOICES["hi"]
    )

    # --------------------------------------------------------
    # GOOGLE TTS
    # --------------------------------------------------------

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

    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # IMPORTANT:
    # response.audio_content is already binary MP3 data.
    # DO NOT .decode(), .encode(), or convert through Latin-1.
    audio_bytes = bytes(response.audio_content)

    if not audio_bytes:
        raise RuntimeError(
            "Google TTS returned an empty audio stream"
        )

    return {
        "resolved_language": target_lang,
        "translated_text": translated_text,
        "audio_bytes": audio_bytes
    }