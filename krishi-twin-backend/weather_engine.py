import os
import json
import requests
import argparse
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# RESILIENT HTTP SESSION
# ============================================================

session = requests.Session()

retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    raise_on_status=False,
)

adapter = HTTPAdapter(max_retries=retries)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
})


# ============================================================
# GOOGLE EARTH ENGINE - SENTINEL-2 NDVI
# ============================================================

def fetch_sentinel2_ndvi(lat: float, lon: float) -> float:
    """
    Fetch live Sentinel-2 NDVI from Google Earth Engine.
    Falls back to 0.37 if GEE is unavailable.
    """

    try:
        import ee

        key_path = "gcp-key.json"

        if os.path.exists(key_path):
            with open(key_path, "r") as f:
                key_data = json.load(f)

            client_email = key_data.get("client_email")
            project_id = key_data.get("project_id")

            if client_email and project_id:
                credentials = ee.ServiceAccountCredentials(
                    client_email,
                    key_path,
                )
                ee.Initialize(
                    credentials,
                    project=project_id,
                )
            else:
                ee.Initialize()
        else:
            ee.Initialize()

        point = ee.Geometry.Point([lon, lat])

        start_date = (
            datetime.now(timezone.utc) - timedelta(days=120)
        ).strftime("%Y-%m-%d")

        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        s2_collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(point)
            .filterDate(start_date, end_date)
            .filter(
                ee.Filter.lt(
                    "CLOUDY_PIXEL_PERCENTAGE",
                    30,
                )
            )
            .sort("system:time_start", False)
        )

        image = s2_collection.first()

        ndvi_image = (
            image
            .normalizedDifference(["B8", "B4"])
            .rename("NDVI")
        )

        stats = ndvi_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point.buffer(200),
            scale=10,
        )

        res = stats.getInfo()

        mean_ndvi = res.get("NDVI") if res else None

        if mean_ndvi is not None:
            mean_ndvi = round(float(mean_ndvi), 4)

            print(
                f"Sentinel-2 Live NDVI Fetched via GEE: {mean_ndvi}",
                flush=True,
            )

            return mean_ndvi

    except Exception as e:
        print(
            "Earth Engine NDVI Query Warning: "
            f"{type(e).__name__} ({e}). "
            "Falling back to baseline model index 0.37.",
            flush=True,
        )

    return 0.37


# ============================================================
# WEATHER ENGINE
# ============================================================

def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch live weather forecast from Open-Meteo.
    Uses the next 24 hours.
    """

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&hourly="
        "precipitation,"
        "precipitation_probability,"
        "wind_speed_10m"
        "&forecast_days=2"
        "&timezone=auto"
    )

    response = session.get(
        weather_url,
        timeout=10,
    )

    response.raise_for_status()

    weather_data = response.json().get(
        "hourly",
        {},
    )

    precipitation = weather_data.get(
        "precipitation",
        [],
    )[:24]

    precipitation_probability = weather_data.get(
        "precipitation_probability",
        [],
    )[:24]

    wind_speed = weather_data.get(
        "wind_speed_10m",
        [],
    )[:24]

    rain_24h_mm = round(
        sum(precipitation),
        2,
    )

    max_rain_prob = max(
        precipitation_probability,
        default=0,
    )

    max_wind_kmh = round(
        max(wind_speed, default=0),
        2,
    )

    wash_off_risk = (
        "HIGH"
        if rain_24h_mm > 10.0 or max_rain_prob > 70
        else "LOW"
    )

    print(
        "\n--- LIVE WEATHER ---",
        flush=True,
    )

    print(
        f"Rain next 24h: {rain_24h_mm} mm",
        flush=True,
    )

    print(
        f"Rain probability: {max_rain_prob}%",
        flush=True,
    )

    print(
        f"Maximum wind: {max_wind_kmh} km/h",
        flush=True,
    )

    print(
        f"Wash-off risk: {wash_off_risk}",
        flush=True,
    )

    return {
        "rainfall_probability": max_rain_prob,
        "rain_next_24h_mm": rain_24h_mm,
        "wind_speed_kmh": max_wind_kmh,
        "washoff_risk": wash_off_risk,
    }


# ============================================================
# MAIN WEATHER / TELEMETRY ENGINE
# ============================================================

def run_weather_engine(
    lat: float = 9.8821,
    lon: float = 78.0815,
    crop: str = "Rice",
    district: str = "Madurai",
    acres: float = 2.0,
    symptom: str = "Leaf Blight",
    spray_cost_override: float = None,
    crop_loss_override: float = None,
    backend_url: str = (
        "http://127.0.0.1:8080/api/v1/simulate"
    ),
) -> dict:

    print(
        "\n=== Running Krishi-Twin Weather & Telemetry Engine ===",
        flush=True,
    )

    print(
        f"Target Location: ({lat}, {lon}) | "
        f"District: {district} | "
        f"Crop: {crop} ({acres} acres)",
        flush=True,
    )

    # --------------------------------------------------------
    # 1. GOOGLE EARTH ENGINE NDVI
    # --------------------------------------------------------

    mean_ndvi = fetch_sentinel2_ndvi(
        lat,
        lon,
    )

    # --------------------------------------------------------
    # 2. LIVE MARKET DATA
    # --------------------------------------------------------

    # --------------------------------------------------------
    # 2. LIVE MARKET DATA
    # --------------------------------------------------------

    gov_api_key = os.getenv("GOV_DATA_API_KEY")

    gov_url = (
        "https://api.data.gov.in/resource/"
        "9ef84268-d588-465a-a308-a864a43d0070"
    )

    market_info = {
        "price_inr_per_kg": 21.0,
        "source": "baseline",
    }

    modal_price_per_kg = 21.0

    if not gov_api_key:
        print(
            "Market Warning: GOV_DATA_API_KEY is not set "
            "in environment/.env file.",
            flush=True,
        )
        print(
            f"Using baseline Rs.{modal_price_per_kg}/kg.",
            flush=True,
        )
    else:
        gov_params = {
            "api-key": gov_api_key,
            "format": "json",
            "filters[district]": district,
            "filters[commodity]": crop,
            "limit": 10,
        }

        print(
            f"Fetching live market rates from data.gov.in "
            f"for {crop} in {district}...",
            flush=True,
        )

        try:
            market_response = session.get(
                gov_url,
                params=gov_params,
                timeout=10,
            )

            market_response.raise_for_status()

            records = market_response.json().get(
                "records",
                [],
            )

            if records:
                latest = records[0]

                modal_price_quintal = float(
                    latest.get("modal_price", 0)
                )

                if modal_price_quintal > 0:
                    modal_price_per_kg = round(
                        modal_price_quintal / 100.0,
                        2,
                    )

                    market_info = {
                        "market": latest.get("market"),
                        "commodity": latest.get("commodity"),
                        "variety": latest.get("variety"),
                        "modal_price_inr_quintal": modal_price_quintal,
                        "price_inr_per_kg": modal_price_per_kg,
                        "arrival_date": latest.get("arrival_date"),
                        "source": "data.gov.in",
                    }

                    print(
                        f"Market Data Fetched: {crop} @ "
                        f"Rs.{modal_price_quintal}/quintal "
                        f"(Rs.{modal_price_per_kg}/kg) "
                        f"at {market_info['market']}",
                        flush=True,
                    )

                else:
                    print(
                        "Market Warning: Invalid modal price. "
                        f"Using baseline Rs.{modal_price_per_kg}/kg.",
                        flush=True,
                    )

            else:
                print(
                    f"Market Warning: No records found for "
                    f"{crop} in {district}. "
                    f"Using baseline Rs.{modal_price_per_kg}/kg.",
                    flush=True,
                )

        except requests.exceptions.Timeout:
            print(
                "Market Warning: data.gov.in request timed out. "
                f"Using baseline Rs.{modal_price_per_kg}/kg.",
                flush=True,
            )

        except requests.exceptions.RequestException as e:
            print(
                f"Market Fetch Warning: {e}. "
                f"Using baseline Rs.{modal_price_per_kg}/kg.",
                flush=True,
            )

        except (ValueError, TypeError) as e:
            print(
                f"Market Data Warning: Invalid response ({e}). "
                f"Using baseline Rs.{modal_price_per_kg}/kg.",
                flush=True,
            )

        except Exception as e:
            print(
                f"Market Processing Warning: {e}. "
                f"Using baseline Rs.{modal_price_per_kg}/kg.",
                flush=True,
            )

    # --------------------------------------------------------
    # 3. FINANCIAL CALCULATIONS
    # --------------------------------------------------------

    spray_cost_inr = (
        spray_cost_override
        if spray_cost_override is not None
        else round(acres * 425.0, 2)
    )

    potential_crop_loss_inr = (
        crop_loss_override
        if crop_loss_override is not None
        else round(
            acres * 100.0 * modal_price_per_kg,
            2,
        )
    )

    print(
        f"Financial Calculations: "
        f"Spray Cost = Rs.{spray_cost_inr} | "
        f"Potential Crop Loss = Rs.{potential_crop_loss_inr}",
        flush=True,
    )

    # --------------------------------------------------------
    # 4. LIVE WEATHER
    # --------------------------------------------------------

    weather = fetch_weather(
        lat,
        lon,
    )

    # --------------------------------------------------------
    # 5. BUILD PAYLOAD
    # --------------------------------------------------------

    payload = {
        "engine": "Krishi-Twin-Decision-Core",

        "timestamp": (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        ),

        "farm_profile": {
            "coordinates": {
                "latitude": lat,
                "longitude": lon,
            },
            "crop": crop,
            "farm_size_acres": acres,
            "detected_symptom": symptom,
        },

        "geospatial_telemetry": {
            "mean_ndvi_index": mean_ndvi,
            "canopy_vigor": (
                "Stressed"
                if mean_ndvi < 0.4
                else "Healthy"
            ),
        },

        "meteorological_risk": weather,

        "market_telemetry": market_info,

        "financial_inputs": {
            "spray_cost_inr": spray_cost_inr,
            "potential_crop_loss_inr": (
                potential_crop_loss_inr
            ),
        },
    }

    # --------------------------------------------------------
    # 6. SHOW PAYLOAD
    # --------------------------------------------------------

    print(
        "\n--- TELEMETRY SENT TO FASTAPI ---",
        flush=True,
    )

    print(
        json.dumps(
            payload,
            indent=2,
        ),
        flush=True,
    )

    # --------------------------------------------------------
    # 7. POST TO FASTAPI
    # --------------------------------------------------------

    print(
        f"\nPosting live payload to backend "
        f"({backend_url})...",
        flush=True,
    )

    sim_response = requests.post(
        backend_url,
        json=payload,
        timeout=60,
    )

    print(
        f"Backend HTTP Status: "
        f"{sim_response.status_code}",
        flush=True,
    )

    print(
        f"Backend Response:\n"
        f"{sim_response.text}",
        flush=True,
    )

    sim_response.raise_for_status()

    result = sim_response.json()

    print(
        "\n--- Live Simulation Result from Backend ---",
        flush=True,
    )

    print(
        json.dumps(
            result,
            indent=2,
        ),
        flush=True,
    )

    return result


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Krishi-Twin Dynamic Telemetry "
            "& Simulation Engine"
        )
    )

    parser.add_argument(
        "--lat",
        type=float,
        default=9.8821,
        help="Latitude coordinate",
    )

    parser.add_argument(
        "--lon",
        type=float,
        default=78.0815,
        help="Longitude coordinate",
    )

    parser.add_argument(
        "--crop",
        type=str,
        default="Rice",
        help="Crop commodity name",
    )

    parser.add_argument(
        "--district",
        type=str,
        default="Madurai",
        help="District name",
    )

    parser.add_argument(
        "--acres",
        type=float,
        default=2.0,
        help="Farm size in acres",
    )

    parser.add_argument(
        "--symptom",
        type=str,
        default="Leaf Blight",
        help="Detected crop symptom",
    )

    parser.add_argument(
        "--spray-cost",
        type=float,
        default=None,
        help="Optional spray cost override",
    )

    parser.add_argument(
        "--crop-loss",
        type=float,
        default=None,
        help="Optional potential crop loss override",
    )

    parser.add_argument(
        "--backend-url",
        type=str,
        default=(
            "http://127.0.0.1:8080/api/v1/simulate"
        ),
        help="FastAPI simulation endpoint URL",
    )

    args = parser.parse_args()

    run_weather_engine(
        lat=args.lat,
        lon=args.lon,
        crop=args.crop,
        district=args.district,
        acres=args.acres,
        symptom=args.symptom,
        spray_cost_override=args.spray_cost,
        crop_loss_override=args.crop_loss,
        backend_url=args.backend_url,
    )