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
        print(f"API Key: {self.api_key}")
        self.base_url = 'https://open-api.bingx.com'

    def _get_sign(self, payload):
        signature = hmac.new(self.api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        print("sign=" + signature)
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
        params.update({
            'timestamp': int(time.time() * 1000),
            'recvWindow': 5000
        })
        # ✅ Convert params to a query string before signing
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
        curr_time = str(int(time.time() * 1000))
        coin = coin.replace('USDT', '')  # Extract only the coin name
        endpoint = '/openApi/wallets/v1/capital/deposit/address'
        method = 'GET'
        paramsMap = {
            "timestamp": curr_time,
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
        payload = {}

        endpoint = '/openApi/wallets/v1/capital/withdraw/apply'
        APIURL = "https://open-api.bingx.com"
        method = 'POST'
        paramsMap = {
            "address": address,
            "addressTag": "None",
            "amount": str(amount),
            "coin": coin,
            "network": network,
            "timestamp": str(int(time.time() * 1000)),
            "walletType": "1"

        }
        paramsStr = self._parseParam(paramsMap)
        url = "%s%s?%s&signature=%s" % (APIURL, endpoint, paramsStr, self._get_sign(paramsStr))
        headers = {
            'X-BX-APIKEY': self.api_key,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response

    def buy_crypto(self, symbol, quantity, price=None, order_type="MARKET"):
        """Place a buy order."""
        endpoint = "/openApi/spot/v1/trade/order"
        paramsMap = {
            "symbol": symbol.replace('USDT', '-USDT'),
            "side": "BUY",
            "type": order_type,
            "quantity": str(quantity),
            "timestamp": str(int(time.time() * 1000))
        }
        if order_type == "LIMIT" and price:
            paramsMap["price"] = str(price)
            paramsMap["timeInForce"] = "GTC"

        result = self._signed_request(method="POST", endpoint=endpoint, params=paramsMap)
        return result

    def sell_crypto(self, symbol, quantity, price=None, order_type="MARKET"):
        """Place a sell order."""
        payload = {}
        timestamp = str(int(time.time() * 1000))

        path = '/openApi/spot/v1/trade/order'
        method = "POST"
        paramsMap = {
            "type": "MARKET",
            "symbol": symbol.replace('USDT', '-USDT'),
            "side": "SELL",
            "quantity": quantity,
            "newClientOrderId": "",
            "recvWindow": 1000,
            "timeInForce": "GTC",
            "timestamp": int(timestamp),
        }
        print(paramsMap)
        paramsStr = self._parseParam(paramsMap)
        return self.send_request(method, path, paramsStr, payload)

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
    asset = bingx_data.get_asset_address(network, coin)
    print(f"Deposit Address: {asset}")

    # ✅ Check balance
    balance = bingx_data.check_balance('POL')
    print(f"Balance: {balance}")

    # ✅ Place a market buy order
    # buy_order = bingx_data.buy_crypto("POLUSDT", 10)
    # print(f"Buy Order: {buy_order}")

    # ✅ Place a market sell order
    sell_order = bingx_data.sell_crypto("POLUSDT", 3)
    print(f"Sell Order: {sell_order}")

    # ✅ Withdraw
    # withdrawal = bingx_data.withdraw("POL", "0x1e269d187c5cc1acc1e25c8eb2938b4690f28038", 1, "POLYGON")
    # print(f"Withdrawal: {withdrawal}")