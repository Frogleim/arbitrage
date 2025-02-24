import time
import requests
import hmac
from hashlib import sha256
import os
from dotenv import load_dotenv

load_dotenv()

APIURL = "https://open-api.bingx.com"



def close_postion(symbol):
    payload = {}
    path = '/openApi/swap/v2/trade/closeAllPositions'
    method = "POST"
    paramsMap = {
    "timestamp": str(int(time.time() * 1000)),
    "symbol": f"{symbol}-USDT"
}
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload)



def get_market_price(symbol):
    """Fetch the latest market price for BTC-USDT."""
    url = f"{APIURL}/openApi/swap/v2/quote/price?symbol={symbol}-USDT"
    response = requests.get(url)
    data = response.json()
    print(data)
    if data.get("code") == 0:
        return True, float(data["data"]["price"])
    else:
        return False, None


def open_trade(symbol, exit_price, quantity, api_key, api_secret):
    """Open a short market order using the current market price as entry."""
    is_valid, entry_price = get_market_price(symbol)
    path = '/openApi/swap/v2/trade/order'
    try:
        if is_valid:
            take_profit = f'{{"type": "TAKE_PROFIT_MARKET", "stopPrice": {exit_price}, "price": {entry_price}, "workingType": "MARK_PRICE"}}'

            method = "POST"
            paramsMap = {
                "symbol": f"{symbol}-USDT",
                "side": "SELL",
                "positionSide": "SHORT",
                "type": "MARKET",
                "quantity": str(10),
                "takeProfit": take_profit,
            }

            paramsStr = parseParam(paramsMap)
            return True, send_request(method, path, paramsStr, {}, api_key, api_secret)
        else:
            return False, None
    except Exception as e:
        return False, e


def get_sign(api_secret, payload):
    """Generate HMAC SHA256 signature."""
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature


def send_request(method, path, urlpa, payload, api_secret, api_key):
    """Send a request to the BingX API."""
    url = f"{APIURL}{path}?{urlpa}&signature={get_sign(api_secret, urlpa)}"
    headers = {
        'X-BX-APIKEY': api_key,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    print(response.json())
    return response.json()


def parseParam(paramsMap):
    """Convert params to a sorted query string."""
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    return paramsStr + "&timestamp=" + str(int(time.time() * 1000))


if __name__ == '__main__':
    try:
        entry_price = get_market_price()
        print(f"Current Market Price: {entry_price}")
        # response = open_trade(exit_price=entry_price * 0.02, quantity=0.01)  # Example TP 2% above
        response = close_postion(symbol='POL')
        print("Trade Response:", response)
    except Exception as e:
        print("Error:", e)