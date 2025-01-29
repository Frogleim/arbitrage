from bingX.spot import Spot
import os
from dotenv import load_dotenv

# Load API credentials from .env file
load_dotenv()

class BingX:
    def __init__(self):
        self.api_key = os.getenv('BINGX_API_KEY')
        self.api_secret = os.getenv('BINGX_SECRET_KEY')
        self.client = Spot(self.api_key, self.api_secret)

    def get_asset_address(self, coin, network):
        """Fetches the deposit contract address for a given coin and network"""
        wallet_assets = self.client.assets(recvWindow=None)  # Adjust if needed
        base_coin = coin.split("/")[0]  # Extract "BTC" from "BTC/USDT"

        for asset in wallet_assets:
            if asset["asset"] == base_coin:
                print("Found asset:", asset)

                for net in asset["networks"]:
                    if network.lower() in net["network"].lower():  # Partial match
                        return net["contract"]  # Return contract address

        return None  # If coin or network is not found

    def check_signal(self, trading_pair):
        """Fetches current price of a trading pair"""
        price_data = self.client.symbols(symbol=trading_pair)
        return price_data

    def withdraw(self, amount, coin, network, address):
        """Withdraws specified amount of crypto to a given address"""
        withdraw_request = self.client.wallet.withdraw(
            asset=coin,
            network=network,
            address=address,
            amount=amount
        )
        return withdraw_request

    def buy_crypto(self, coin, quote_coin, amount):
        """Places a market buy order"""
        trading_pair = f"{coin}{quote_coin}"  # Example: "BTCUSDT"

        order = self.client.trade.new_order(
            symbol=trading_pair,
            side="BUY",
            type="MARKET",
            quoteOrderQty=amount  # Amount in quote currency (USDT)
        )
        return order

    def check_balance(self, coin):
        """Checks the available balance for a given asset"""
        balances = self.client.account.get_account()["balances"]
        for asset in balances:
            if asset["asset"] == coin:
                return asset  # Returns full balance details
        return None

    def sell_crypto(self, coin, quote_coin, amount):
        """Places a market sell order"""
        trading_pair = f"{coin}{quote_coin}"  # Example: "BTCUSDT"

        order = self.client.trade.new_order(
            symbol=trading_pair,
            side="SELL",
            type="MARKET",
            quoteOrderQty=amount  # Amount in quote currency (USDT)
        )
        return order


if __name__ == '__main__':
    bingx_data = BingX()
    coin = 'CGPT/USDT'
    network = 'BEP20'
    asset = bingx_data.get_asset_address(coin, network)
    print(asset)