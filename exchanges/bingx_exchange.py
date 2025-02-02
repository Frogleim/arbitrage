from bingX.spot import Spot
import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
import hmac
from hashlib import sha256

import time

load_dotenv()

class BingX:
    def __init__(self):
        self.api_key = os.getenv('BINGX_API_KEY')
        self.api_secret = os.getenv('BINGX_SECRET_KEY')
        self.client = Spot(self.api_key, self.api_secret)
        print(f"API Key: {self.api_key}")
        print(f"API Secret: {self.api_secret}")
        self.base_url = 'https://open-api.bingx.com'

    def _get_sign(self, params):
        """Generate a signature for the API request"""
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"),
                             digestmod=sha256).hexdigest()
        return signature

    def _signed_request(self, method, endpoint, params=None):
        params = params or {}
        params.update({
            'timestamp': int(time.time() * 1000),
            'recvWindow': 5000
        })
        signature = self._get_sign(params)
        params['signature'] = signature
        headers = {'X-BX-APIKEY': self.api_key}
        url = f"{self.base_url}{endpoint}"
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, json=params, headers=headers)
        return response.json()

    def get_asset_address(self, network, coin):
        curr_time = str(int(time.time() * 1000))
        coin = coin.replace('USDT', '')  # Extract only the coin name
        endpoint = '/openApi/wallets/v1/capital/config/getall'
        method = 'GET'
        paramsMap = {
            "timestamp": curr_time
        }

        result = self._signed_request(method=method, endpoint=endpoint, params=paramsMap)

        for data in result['data']:
            if data['name'] == coin:
                print(data['networkList'])
                address = data['networkList']
                return address

    def check_signal(self, trading_pair, price=None, threshold=0.02):
        curr_time = str(int(time.time() * 1000))
        coin = trading_pair.replace('USDT', '-USDT')  # Extract only the coin name
        endpoint = '/openApi/spot/v1/ticker/price'
        method = 'GET'
        paramsMap = {
            "timestamp": curr_time,
            "symbol": coin
        }

        result = self._signed_request(method=method, endpoint=endpoint, params=paramsMap)
        print(result)
        market_price = result['data'][0]['trades'][0]['price']
        diff = abs(price - float(market_price)) / float(market_price)
        is_near = diff <= threshold
        print(is_near)
        return {
            "market_price": market_price,
            "incoming_price": price,
            "difference": diff * 100,  # Convert to percentage
            "is_near": is_near
        }


    def withdraw(self):
        pass

    def buy_crypto(self):
        pass

    def check_balance(self):
        pass

    def sell_crypto(self):
        pass



if __name__ == '__main__':

    bingx_data = BingX()
    coin = 'BTCUSDT'
    network = 'BEP20'
    # asset = bingx_data.get_asset_address(network, coin)  # ✅ Correct
    # print(asset)
    data = bingx_data.check_signal(coin, 98190)
    print(data)