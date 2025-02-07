import os
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
import hmac
from hashlib import sha256
import time
from .get_api import sell
import urllib.parse
from .bingx_buy import buy_crypto
from .bingx_withraw import withdraw
from .bingx_sell import sell

import hashlib

load_dotenv()


class BingX:
    def __init__(self):
        self.api_key = os.getenv('BINGX_API_KEY')
        self.api_secret = os.getenv('BINGX_SECRET_KEY')
        print(f"API Key: {self.api_key}")
        self.base_url = 'https://open-api.bingx.com'

    def _get_sign(self, params):
        """Generate HMAC SHA256 signature for BingX API"""
        # Sort the dictionary by keys and URL-encode it
        query_string = urllib.parse.urlencode(sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def _parseParam(paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        if paramsStr != "":
            return paramsStr + "&timestamp=" + str(int(time.time() * 1000))
        else:
            return paramsStr + "timestamp=" + str(int(time.time() * 1000))

    def send_request(self, method, path, urlpa, payload):
        url = "%s%s?%s&signature=%s" % (self.base_url, path, urlpa, self._get_sign(urlpa))
        print(url)
        headers = {
            'X-BX-APIKEY': self.api_key,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response.text

    def _signed_request(self, method, endpoint, params=None):
        params = params or {}
        # Only add 'timestamp' if it is not already provided.
        if 'timestamp' not in params:
            params['timestamp'] = int(time.time() * 1000)
        # Add recvWindow only if the API endpoint expects it.
        if endpoint not in ['/openApi/wallets/v1/capital/deposit/address']:
            params.setdefault('recvWindow', 5000)

        # Generate signature over the exact parameters
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
        """Fetch the deposit address for a given coin and network."""
        # Remove "USDT" if that’s how your coin names are expected.
        coin = coin.replace('USDT', '')
        endpoint = '/openApi/wallets/v1/capital/deposit/address'
        method = 'GET'
        paramsMap = {
            "coin": coin,
        }
        result = self._signed_request(method=method, endpoint=endpoint, params=paramsMap)
        print(result)  # Debugging

        for data in result.get('data', {}).get('data', []):
            if data['coin'] == coin and network == data['network']:
                return data.get('addressWithPrefix', 'No address found')
        return None

    def check_signal(self, trading_pair, price=None, threshold=0.02):
        """Check market price and compare it with the incoming price."""
        curr_time = str(int(time.time() * 1000))
        coin = trading_pair.replace('USDT', '-USDT')  # Format symbol
        endpoint = '/openApi/spot/v1/ticker/price'
        method = 'GET'
        paramsMap = {
            "timestamp": curr_time,
            "symbol": coin
        }

        result = self._signed_request(method=method, endpoint=endpoint, params=paramsMap)
        print(result)
        market_price = float(result['data'][0]['trades'][0]['price'])
        diff = abs(price - market_price) / market_price
        is_near = diff <= threshold

        return {
            "market_price": market_price,
            "incoming_price": price,
            "difference": diff * 100,  # Convert to percentage
            "is_near": is_near
        }

    def withdraw(self, coin, address, amount, network):
        """Withdraw crypto to a given address."""
        withdraw(address, coin, amount, network)
        return True

    def buy_crypto(self, symbol, quantity, price=None, order_type="MARKET"):
        """Place a buy order."""
        res = buy_crypto(symbol, quantity)
        return res

    def sell_crypto(self, symbol, quantity, price=None, order_type="MARKET"):
        """Place a sell order."""
        return sell(coin=symbol, quantity=float(quantity))

    def check_balance(self, coin=None):
        """Retrieve account balance. If `coin` is provided, return balance for that coin."""
        endpoint = "/openApi/spot/v1/account"
        paramsMap = {
            "timestamp": str(int(time.time() * 1000))
        }

        result = self._signed_request(method="GET", endpoint=endpoint, params=paramsMap)

        if coin:
            for asset in result.get('data', {}).get('balances', []):
                if asset['asset'] == coin:
                    return asset

        return result


if __name__ == '__main__':
    bingx_data = BingX()

    # ✅ Get deposit address
    coin = 'POLUSDT'
    network = 'POLYGON'
    # asset = bingx_data.get_asset_address(network, coin)
    # print(f"Deposit Address: {asset}")
    #
    # # ✅ Check balance
    # balance = bingx_data.check_balance('POL')
    # print(f"Balance: {balance}")
    #
    # # ✅ Place a market buy order
    # buy_order = bingx_data.buy_crypto("POLUSDT", 10)
    # print(f"Buy Order: {buy_order}")

    # # ✅ Place a market sell order
    sell_order = bingx_data.sell_crypto("POLUSDT", 3)
    print(f"Sell Order: {sell_order}")

    # # ✅ Withdraw
    # withdrawal = bingx_data.withdraw("POL", "0x1e269d187c5cc1acc1e25c8eb2938b4690f28038", 1, "POLYGON")
    # print(f"Withdrawal: {withdrawal}")