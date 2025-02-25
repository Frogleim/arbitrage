import time
import requests
import hmac
from hashlib import sha256
import loggs

APIURL = "https://open-api.bingx.com"


def close_position(symbol, api_key, api_secret):
    payload = {}
    path = '/openApi/swap/v2/trade/closeAllPositions'
    method = "POST"
    paramsMap = {
        "timestamp": str(int(time.time() * 1000)),
        "symbol": f"{symbol}-USDT"
    }
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload, api_key, api_secret)


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


def set_leverage(symbol,  api_key, api_secret, leverage=10):

    """Setting coin leverage."""

    payload = {}
    path = '/openApi/swap/v2/trade/leverage'
    method = "POST"
    paramsMap = {
    "leverage": str(leverage),
    "side": "SHORT",
    "symbol": f"{symbol}-USDT",
    "timestamp": str(int(time.time() * 1000))
}
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload, api_key, api_secret)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def open_trade(symbol, exit_price, quantity, api_key, api_secret):
    """Open a short market order using the current market price as entry."""
    try:
        is_valid, entry_price = get_market_price(symbol)
        if is_valid:
            res = set_leverage(symbol, api_key, api_secret)
            loggs.system_log.info(f"leverage={res}")
            exit_price = float(exit_price) * 0.9
            path = '/openApi/swap/v2/trade/order'

            take_profit = f'{{"type": "TAKE_PROFIT_MARKET", "stopPrice": {exit_price}, "price": {entry_price}, "workingType": "MARK_PRICE"}}'

            method = "POST"
            paramsMap = {
                "symbol": f"{symbol}-USDT",
                "side": "SELL",
                "positionSide": "SHORT",
                "type": "MARKET",
                "quantity": 10,
                "takeProfit": take_profit,
            }

            paramsStr = parseParam(paramsMap)
            return True, 'Ok'
        else:
            return False, None

    except Exception as e:
        return False, str(e)



def get_sign(api_secret, payload):
    """Generate HMAC SHA256 signature."""
    return hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()


def send_request(method, path, urlpa, payload, api_key, api_secret):
    """Send a request to the BingX API with passed API credentials."""
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
        # Use your API keys
        BINGX_API_KEY = "B4Ugtf2PRyE9lOjr8QEWS0OmjLR4D1LueKhhkupGBOTU9dAjMVShOJNKmAtnjkc0Yh6NhSyZjI4rIIFfmsXLQ"
        BINGX_SECRET_KEY = "b57tloU10BxiNpc6sKe6kiue9tSxws8WLMkv4hABkitBPBOP5hAV6WalzR2YrwKRuLvE26h6xNuLOXb8MmgQ"

        entry_price = get_market_price(symbol='BTC')
        print(f"Current Market Price: {entry_price}")

        response = open_trade(
            symbol='BTC',
            exit_price=entry_price,  # Example TP 2% above
            quantity=0.01,
            api_key=BINGX_API_KEY,
            api_secret=BINGX_SECRET_KEY
        )

        print("Trade Response:", response)
    except Exception as e:
        print("Error:", e)


        # B4Ugtf2PRyE9lOjr8QEWS0OmjLR4D1LueKhhkupGBOTU9dAjMVShOJNKmAtnjkc0Yh6NhSyZjI4rIIFfmsXLQ
        # b57tloU10BxiNpc6sKe6kiue9tSxws8WLMkv4hABkitBPBOP5hAV6WalzR2YrwKRuLvE26h6xNuLOXb8MmgQ