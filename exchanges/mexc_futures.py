import time
import requests
import hmac
import os
from hashlib import sha256
from dotenv import load_dotenv
from urllib.parse import urlencode

# ✅ Load environment variables
load_dotenv()

# ✅ MEXC API credentials
APIURL = "https://contract.mexc.com"
APIKEY = os.getenv('MEX_API_KEY')
SECRETKEY = os.getenv('MEX_SECRET_KEY')


def get_timestamp():
    """Returns the current timestamp in milliseconds."""
    return str(int(time.time() * 1000))


def get_signature(api_secret, payload):
    """Generates HMAC SHA256 signature for authentication."""
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
    print(f"🔍 Signature: {signature}")  # ✅ Debugging
    return signature


def send_request(method, endpoint, params):
    """Send a signed request to the MEXC API."""
    url = f"{APIURL}{endpoint}?{params}&signature={get_signature(SECRETKEY, params)}"

    headers = {
        "X-MEXC-APIKEY": APIKEY,
    }

    print(f"🔍 Sending Request to: {url}")  # ✅ Debugging

    response = requests.request(method, url, headers=headers)
    return response.json()


def withdraw(coin, address, amount, network, memo=None):
    """Withdraw funds from MEXC."""
    timestamp = get_timestamp()

    # ✅ Construct API parameters
    params_map = {
        "symbol": coin,  # ✅ Ensure correct coin format
        "price": address,
        "vol": str(amount),  # ✅ Ensure amount is a string
        "side": network,
        "type": timestamp,
        "openType": "cross",

    }

    # ✅ Include memo if available
    if memo:
        params_map["memo"] = memo

    # ✅ Generate sorted query string
    params_str = urlencode(sorted(params_map.items()))

    # ✅ Send POST request to MEXC API
    return send_request("POST", "/api/v1/private/order/submit", params_str)


# ✅ Example Usage
if __name__ == "__main__":
    response = withdraw(
        coin="POL",  # ✅ Check correct coin symbol using `fetch_currencies`
        address="0x1e269d187c5cc1acc1e25c8eb2938b4690f28038",
        amount=1,
        network="Polygon(MATIC)"  # ✅ Ensure this matches MEXC-supported networks
    )

    print(f"🔍 Withdraw Response: {response}")  # ✅ Debugging