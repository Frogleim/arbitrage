
import time
import requests
import hmac
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""


token_list = ['BANANA', 'OP']


def get_market_price(symbol):

    """Fetch the latest market price for BTC-USDT."""
    url = f"{APIURL}/openApi/swap/v2/quote/price?symbol={symbol}-USDT"
    response = requests.get(url)
    data = response.json()
    if data.get("code") == 0:
        return True, float(data["data"]["price"])
    else:
        return False, None

def demo():
    for token in token_list:
        payload = {}
        path = '/openApi/swap/v1/market/markPriceKlines'
        method = "GET"
        paramsMap = {
        "symbol": f"{token}-USDT",
        "interval": "1h",
        "limit": "1000",
        "startTime": str(int(time.time() * 1000))
    }
        paramsStr = parseParam(paramsMap)
        return send_request(method, path, paramsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "": 
     return paramsStr+"&timestamp="+str(int(time.time() * 1000))
    else:
     return paramsStr+"timestamp="+str(int(time.time() * 1000))



def arbitrage_v3():
    from exchanges.MEXC import mexc_exchange
    # print("demo:", demo())
    from exchanges.Binance import spot, futures
    from exchanges.BingX import bingx_buy
    bingx_api_key = ''
    bingx_api_secret = ''

    mexc = mexc_exchange.Mexc(
        api_key='mx0vglFXKQlvzxMy6T',
        api_secret='4004ef44894b45cdbfba900079a4c5f2',
    )
    for token in token_list:
        bingx_futures = get_market_price(token)
        bingx_spot = bingx_buy.get_market_price(token, api_key=bingx_api_key, api_secret=bingx_api_secret)
        print(f'BingX last price {token}:', bingx_futures)
        print(f'BingX last spot {token}:', bingx_spot['data'][0]['trades'][0]['price'])
        # last_price = mexc.get_last_price(symbol=token)
        # print(f"last_price MEXC {token}", last_price)
        binance_spot_price = futures.get_market_price(token)
        binance_futures_price = futures.get_market_price(token)
        print(f'price Binance Spot {token}', binance_spot_price)
        print(f'price Binance Futures {token}', binance_futures_price)
        # Check for Arbitrage Opportunities
        signal_data = {}
        # if float(binance_spot_price) < bingx_futures[1]:
        #     print(f"📉 Binance Spot Price {binance_spot_price} for {token} is LOWER than BingX Futures {bingx_futures}! Potential Arbitrage!")
        #     signal_data = {'exchange_from': 'Binance', 'price_from': binance_spot_price, 'quantity_from': 26430, 'orders_count_from': '9', 'exchange_to': 'BingX', 'price_to': bingx_futures, 'quantity_to': 26390, 'orders_count_to': '19', 'token': token}
        #     return signal_data, True

        if float(binance_futures_price) < bingx_futures[1]:
            print(f"📉 Binance Futures Price {binance_futures_price} for {token} is LOWER than BingX Spot {bingx_spot}! Potential Arbitrage!")
            signal_data = {'exchange_from': 'BingX', 'price_from': bingx_spot, 'quantity_from': 26430, 'orders_count_from': '9', 'exchange_to': 'Binance', 'price_to': binance_futures_price, 'quantity_to': 26390, 'orders_count_to': '19', 'token': token}
            return signal_data, True
        return None, False

if __name__ == '__main__':
    while True:
        arbitrage_v3()
        time.sleep(10)