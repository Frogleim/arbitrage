import time
import requests
import hmac
import json  # Import JSON for saving data
import os
from hashlib import sha256
from dotenv import load_dotenv

load_dotenv()

APIURL = "https://open-api.bingx.com"
APIKEY = os.getenv('BINGX_API_KEY')
SECRETKEY = os.getenv('BINGX_SECRET_KEY')


def demo():
    """Fetch data and save it to a JSON file."""
    path = '/openApi/wallets/v1/capital/config/getall'
    method = "GET"
    paramsMap = {
        "timestamp": str(int(time.time() * 1000))
    }
    paramsStr = parseParam(paramsMap)
    response_data = send_request(method, path, paramsStr)

    if response_data and "data" in response_data:
        save_to_json(response_data["data"])

    return response_data


def get_sign(api_secret, payload):
    """Generate HMAC SHA256 signature."""
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()


def send_request(method, path, url_params):
    """Send request to BingX API."""
    url = f"{APIURL}{path}?{url_params}&signature={get_sign(SECRETKEY, url_params)}"
    headers = {'X-BX-APIKEY': APIKEY}

    try:
        response = requests.request(method, url, headers=headers)
        response.raise_for_status()  # Raise error if request fails
        data = response.json()

        if "data" in data and data["data"]:
            print("✅ Data retrieved successfully.")
        else:
            print("⚠️ No data found in response.")

        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def parseParam(paramsMap):
    """Convert parameters dictionary to a sorted query string."""
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    return paramsStr + "&timestamp=" + str(int(time.time() * 1000))


def save_to_json(data, filename="bingx_data.json"):
    """Save data to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"📂 Data saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save JSON: {e}")


if __name__ == '__main__':
    print("🔄 Fetching BingX data...")
    demo()