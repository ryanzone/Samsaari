import requests
import json

url = "https://farmer.in/api/open/prices.json"

headers = {
    "User-Agent": "Samsaari-KrishiTwin/1.0",
    "Accept": "application/json"
}

r = requests.get(
    url,
    headers=headers,
    timeout=30
)

print("STATUS:", r.status_code)

if r.ok:
    data = r.json()

    print(json.dumps(data, indent=2)[:20000])
else:
    print(r.text[:5000])