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
# GOOGLE CLOUD CLIENTS
# ============================================================

translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient()


# ============================================================
# FREE REVERSE GEOCODING
# ============================================================

NOMINATIM_URL = (
    "https://nominatim.openstreetmap.org/reverse"
)


@lru_cache(maxsize=512)
def _reverse_geocode_state(
    latitude_rounded: float,
    longitude_rounded: float
) -> str | None:

    """
    Convert GPS coordinates into a state using
    OpenStreetMap Nominatim.

    No Google Maps API key or billing is required.
    """

    params = {
        "lat": latitude_rounded,
        "lon": longitude_rounded,
        "format": "json",
        "zoom": 10,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "Samsaari-KrishiTwin/1.0"
    }

    try:

        # Nominatim has a strict public-service usage policy and can
        # temporarily return HTTP 429 when requests arrive too quickly.
        # Retry slowly instead of failing the entire Samsaari simulation.
        response = None
        for attempt in range(3):
            response = requests.get(
                NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code != 429:
                break

            wait_seconds = 2 + (attempt * 2)
            print(
                f"Nominatim rate-limited (HTTP 429). "
                f"Retrying in {wait_seconds}s..."
            )
            import time
            time.sleep(wait_seconds)

        response.raise_for_status()

        data = response.json()

        print("NOMINATIM RESPONSE:")
        print(data)

        address = data.get(
            "address",
            {}
        )

        state = address.get(
            "state"
        )

        if state:

            state = state.strip()

            print(
                f"Reverse geocoding state: {state}"
            )

            return state

        print(
            "Reverse geocoding succeeded, "
            "but state was not found."
        )

        return None

    except requests.RequestException as exc:

        print(
            f"Reverse geocoding request failed: {exc}"
        )

        return None

    except Exception as exc:

        print(
            f"Unexpected reverse geocoding error: {exc}"
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
    Resolve regional advisory language from GPS coordinates.

    GPS coordinates are reverse-geocoded to determine the
    state, and the state is mapped to the regional language.
    """

    try:

        lat = float(lat)
        lon = float(lon)

    except (TypeError, ValueError):

        print(
            "Invalid coordinates. "
            "Falling back to Hindi."
        )

        return "hi"

    if not (-90 <= lat <= 90):

        print(
            f"Invalid latitude: {lat}"
        )

        return "hi"

    if not (-180 <= lon <= 180):

        print(
            f"Invalid longitude: {lon}"
        )

        return "hi"

    # Round to ~100 m so tiny GPS movements during a presentation
    # reuse the same reverse-geocoding result instead of repeatedly
    # calling the public Nominatim service.
    rounded_lat = round(lat, 3)
    rounded_lon = round(lon, 3)

    state = _reverse_geocode_state(
        rounded_lat,
        rounded_lon
    )

    if not state:

        print(
            "Could not determine state. "
            "Using Hindi fallback."
        )

        return "hi"

    state_normalized = state.strip()

    language = STATE_LANGUAGE_MAP.get(
        state_normalized,
        "hi"
    )

    print(
        f"Regional geofence: "
        f"({lat}, {lon}) -> "
        f"{state_normalized} -> "
        f"{language}"
    )

    return language


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _validate_text(
    raw_text: str
) -> str:

    if raw_text is None:

        raise ValueError(
            "raw_text cannot be None"
        )

    if not isinstance(
        raw_text,
        str
    ):

        raw_text = str(
            raw_text
        )

    raw_text = raw_text.strip()

    if not raw_text:

        raise ValueError(
            "raw_text cannot be empty"
        )

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
    Translate and synthesize agricultural advisory
    according to the GPS-derived regional language.

    Returns:
        resolved_language
        translated_text
        audio_bytes
    """

    raw_text = _validate_text(
        raw_text
    )

    # --------------------------------------------------------
    # RESOLVE REGIONAL LANGUAGE
    # --------------------------------------------------------

    target_lang = (
        resolve_language_from_coordinates(
            lat,
            lon
        )
    )

    print(
        f"Audio target language: "
        f"{target_lang}"
    )

    # --------------------------------------------------------
    # TRANSLATION
    # --------------------------------------------------------

    translated_text = raw_text

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

        if not isinstance(
            translated_text,
            str
        ):

            translated_text = str(
                translated_text
            )

    print(
        f"Translated advisory: "
        f"{translated_text}"
    )

    # --------------------------------------------------------
    # VOICE SELECTION
    # --------------------------------------------------------

    voice_config = REGIONAL_VOICES.get(
        target_lang,
        REGIONAL_VOICES["hi"]
    )

    # --------------------------------------------------------
    # GOOGLE CLOUD TTS
    # --------------------------------------------------------

    synthesis_input = (
        texttospeech.SynthesisInput(
            text=translated_text
        )
    )

    voice = (
        texttospeech.VoiceSelectionParams(
            language_code=voice_config[
                "language_code"
            ],
            name=voice_config[
                "name"
            ],
            ssml_gender=voice_config[
                "ssml_gender"
            ]
        )
    )

    audio_config = (
        texttospeech.AudioConfig(
            audio_encoding=(
                texttospeech.AudioEncoding.MP3
            ),
            speaking_rate=0.90
        )
    )

    response = (
        tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
    )

    audio_bytes = bytes(
        response.audio_content
    )

    if not audio_bytes:

        raise RuntimeError(
            "Google TTS returned "
            "an empty audio stream"
        )

    print(
        f"TTS generated "
        f"{len(audio_bytes)} bytes "
        f"using "
        f"{voice_config['language_code']}"
    )

    return {
        "resolved_language": target_lang,
        "translated_text": translated_text,
        "audio_bytes": audio_bytes
    }