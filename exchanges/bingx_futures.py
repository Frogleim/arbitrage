import time
import requests
import hmac
from hashlib import sha256
# import loggs
from . import loggs
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

def open_trade(symbol, exit_price, api_key, api_secret, quantity=None):
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
            res = send_request(method, path, paramsStr, {}, api_key, api_secret)
            loggs.system_log.info(res)
            if 'code' in res:
                return True, 'Ok'
            else:
                return False, 'Error'
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


    close_position(symbol='AIXBT', api_key='8q6nlIOLurINPrWH2nnmNhO9SOsvA6kXtuR0DKRv81nWR2erWuZhTjhH9qxOA34HXb3oRLwhsGgb0WmqyDMA', api_secret='Db4epCQmHnqiHS4DJIgfeNHkTuimZdPuC41K0nJx8nMXFDIgqiJEePhPPvgiynbrZowvMAyd46c4RoLlwWvQ')


        # B4Ugtf2PRyE9lOjr8QEWS0OmjLR4D1LueKhhkupGBOTU9dAjMVShOJNKmAtnjkc0Yh6NhSyZjI4rIIFfmsXLQ
        # b57tloU10BxiNpc6sKe6kiue9tSxws8WLMkv4hABkitBPBOP5hAV6WalzR2YrwKRuLvE26h6xNuLOXb8MmgQ