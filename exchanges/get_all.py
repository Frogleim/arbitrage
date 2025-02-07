import requests
import os
import time
import hmac
import hashlib
from dotenv import load_dotenv

# ✅ Load API Keys
load_dotenv()
APIKEY = os.getenv('MEX_API_KEY')
SECRETKEY = os.getenv('MEX_SECRET_KEY')  # Make sure to add your secret key in .env

# ✅ Create timestamp and query string
timestamp = int(time.time() * 1000)
# For this endpoint, if no additional parameters are required,
# your query string might just contain the timestamp.
query_string = f"timestamp={timestamp}"

# ✅ Generate signature using HMAC SHA256
signature = hmac.new(
    SECRETKEY.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Append the signature to the query string
full_query_string = f"{query_string}&signature={signature}"

# ✅ Construct the full URL with query parameters
url = f"https://api.mexc.com/api/v3/capital/config/getall?{full_query_string}"

# ✅ Set headers including your API key
headers = {"X-MEXC-APIKEY": APIKEY}

# ✅ Send GET request
response = requests.get(url, headers=headers)
currencies = response.json()

# ✅ Print response
print("🔍 Supported Coins & Networks on MEXC:")
print(currencies)