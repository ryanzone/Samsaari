import json
import ee

KEY_PATH = "gcp-key.json"

print("=== GEE VERIFICATION ===")

# Load service-account key
with open(KEY_PATH, "r") as f:
    key_data = json.load(f)

client_email = key_data["client_email"]
project_id = key_data["project_id"]

print(f"Service Account: {client_email}")
print(f"Project ID: {project_id}")

try:
    # Authenticate exactly the same way as weather_engine.py
    credentials = ee.ServiceAccountCredentials(
        client_email,
        KEY_PATH
    )

    ee.Initialize(
        credentials,
        project=project_id
    )

    print("\n[1] Earth Engine initialization: SUCCESS")

    # Simple server-side EE test
    point = ee.Geometry.Point([80.07, 12.84])

    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(point)
        .filterDate("2026-01-01", "2026-09-27")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        .sort("system:time_start", False)
        .first()
    )

    print("[2] Sentinel-2 query: SUCCESS")

    # Force Earth Engine to actually execute the request
    info = image.getInfo()

    if info is None:
        print("[3] Result: NO IMAGE FOUND")
    else:
        print("[3] Result: IMAGE FOUND")
        print("    Image ID:", info.get("id"))

    # NDVI test
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

    stats = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point.buffer(200),
        scale=10
    )

    result = stats.getInfo()

    print("[4] NDVI query: SUCCESS")
    print("    NDVI:", result.get("NDVI"))

    print("\n=== GEE IS WORKING ===")

except Exception as e:
    print("\n=== GEE VERIFICATION FAILED ===")
    print(type(e).__name__)
    print(e)