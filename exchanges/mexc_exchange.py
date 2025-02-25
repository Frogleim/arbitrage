import time
import hmac
import hashlib
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
from .mexc_withdraw import withdraw

load_dotenv()


class Mexc:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.mexc.com"

    def _create_signature(self, params):
        """Create HMAC SHA256 signature for MEXC API."""
        query_string = urlencode(params)
        return hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    def _send_request(self, method, endpoint, params=None):
        """Send a request to MEXC API."""
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MEXC-APIKEY": self.api_key}
        params["timestamp"] = str(int(time.time() * 1000))
        params["signature"] = self._create_signature(params)

        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, params=params)
        else:
            raise ValueError("Unsupported HTTP method")
        print(response.json())
        return response.json()

    # ✅ Get Deposit Address
    def get_asset_address(self, coin, network):
        """Retrieve deposit address for a given coin and network."""
        endpoint = "/api/v3/capital/deposit/address"
        params = {"coin": coin, "network": network}
        response = self._send_request("GET", endpoint, params)
        return response[0]['address']

    def get_last_price(self, symbol):
        """Retrieve last price for a given symbol."""
        endpoint = "/api/v3/ticker/price"
        params = {"symbol": f"{symbol}USDT"}
        response = self._send_request("GET", endpoint, params)
        return response['price']

    # ✅ Get Market Price
    def check_signal(self, trading_pair, price, threshold=0.02):
        """Check if the price is near a given threshold."""
        endpoint = "/api/v3/ticker/price"
        params = {"symbol": trading_pair}
        response = self._send_request("GET", endpoint, params)

        market_price = float(response["price"])
        diff = abs(price - market_price) / market_price
        is_near = diff <= threshold

        return {
            "market_price": market_price,
            "incoming_price": price,
            "difference": diff * 100,
            "is_near": is_near
        }

    # ✅ Withdraw Crypto
    def withdraw(self, amount, coin, network, address):
        is_withdraw = withdraw(
            coin=coin,
            address=address,
            amount=amount,
            network=network,
        )
        return is_withdraw

    # ✅ Buy Crypto
    def buy_crypto(self, coin, price=None, amount=None):
        """Place a market buy order."""
        last_price = self.get_last_price(coin)
        endpoint = "/api/v3/order"
        params = {
            "symbol": f"{coin}USDT",
            "side": "BUY",
            "type": "MARKET",
            # "price": price,
            "quoteOrderQty": str(10)
        }
        response = self._send_request("POST", endpoint, params)
        return response

    # ✅ Get Account Balance
    def check_balance(self, coin):
        """Check account balance for a specific coin."""
        endpoint = "/api/v3/account"
        params = {}
        response = self._send_request("GET", endpoint, params)
        return response


    # ✅ Sell Crypto
    def sell_crypto(self, coin, amount):
        """Sell a cryptocurrency."""
        endpoint = "/api/v3/order"
        params = {
            "symbol": coin,
            "side": "SELL",
            "type": "MARKET",
            "quoteOrderQty": str(amount)
        }
        response = self._send_request("POST", endpoint, params)
        return response

    # ✅ Get Assets by Address
    def get_assets_by_address(self, target_address):
        """Retrieve assets associated with a specific address."""
        endpoint = "/api/v3/capital/config/getall"
        params = {}
        response = self._send_request("GET", endpoint, params)

        matching_assets = []
        for asset in response:
            for net in asset.get("networkList", []):
                if net.get("contract") == target_address:
                    matching_assets.append({
                        "coin": asset["coin"],
                        "network": net["network"],
                        "contract": net["contract"]
                    })
        return matching_assets


if __name__ == '__main__':
    from decimal import Decimal, ROUND_DOWN


    def round_amount(amount, decimals=2):
        return Decimal(amount).quantize(Decimal(f'1.{"0" * decimals}'), rounding=ROUND_DOWN)


    MEX_API_KEY = 'mx0vglFXKQlvzxMy6T'
    MEX_SECRET_KEY = '4004ef44894b45cdbfba900079a4c5f2'

    mexc_data = Mexc(MEX_API_KEY, MEX_SECRET_KEY)

    # ✅ Get deposit address
    deposit_address = mexc_data.get_asset_address('POL', 'Polygon(MATIC)')
    print(f"Deposit Address: {deposit_address}")

    # # ✅ Get MATIC/USDT market price
    # price_data = mexc_data.check_signal("MATICUSDT", price=1.0)
    # print(price_data)
    #
    # # ✅ Withdraw MATIC to an external address
    # withdraw_response = mexc_data.withdraw(
    #     amount="1",
    #     coin="MATIC",
    #     network="POLYGON",
    #     address="0x1e269d187c5cc1acc1e25c8eb2938b4690f28038"
    # )
    # print(withdraw_response)
    #
    # # ✅ Buy crypto (Market order)
    # buy_response = mexc_data.buy_crypto("B3", amount=10)
    # print(buy_response)
    # #
    # # ✅ Check account balance
    balance = mexc_data.check_balance("MATIC")
    print(f"Balance: {balance}")
    #
    # # ✅ Sell crypto (Market order)
    # sell_response = mexc_data.sell_crypto("MATICUSDT", amount=5)
    # print(sell_response)