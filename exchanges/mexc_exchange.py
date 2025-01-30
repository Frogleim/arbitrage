from mexc_api.spot import Spot
import os
from dotenv import load_dotenv
from mexc_api.common.enums import Side, OrderType, StreamInterval, Action


load_dotenv()

class Mexc:
    def __init__(self):
        self.api_key = os.getenv('MEX_API_KEY')
        self.api_secret = os.getenv('MEX_SECRET_KEY')
        self.client = Spot(self.api_key, self.api_secret)

    def get_asset_address(self, coin, network):
        # Fetch wallet asset info
        wallet_assets = self.client.wallet.info()
        base_coin = coin.split("/")[0]  # Extracts "CGPT" from "CGPT/USDT"

        # Loop through assets to find the correct coin
        for asset in wallet_assets:
            if asset["coin"] == base_coin:

                # Loop through available networks
                for net in asset["networkList"]:
                    if network.lower() in net["network"].lower():  # Partial match
                        return net["contract"]  # Return the contract address

        return None  # If coin or network is not found

    def check_signal(self, trading_pair, price, threshold=0.02):  # 0.5% threshold
        price_data = self.client.market.ticker_price(symbol=trading_pair)
        market_price = float(price_data[0]['price'])  # Convert to float
        diff = abs(price - market_price) / market_price

        # Check if the price is within the threshold
        is_near = diff <= threshold

        return {
            "market_price": market_price,
            "incoming_price": price,
            "difference": diff * 100,  # Convert to percentage
            "is_near": is_near
        }

    def withdraw(self, amount, coin, network, address):
        withdraw_amount = self.client.wallet.withdraw(
            asset=coin,
            network=network,
            address=address,
            amount=amount
        )
        return withdraw_amount

    def buy_crypto(self, coin,  amount):
        print(coin)
        order = self.client.account.new_order(
            symbol=coin,
            side=Side.BUY,  # Buy order
            order_type=OrderType.MARKET,  # Market order
            quote_order_quantity=amount  # Amount in quote currency (USDT)
        )
        return order

    def check_balance(self, coin):
        balances = self.client.account.get_account()["balances"]
        for asset in balances:
            if asset["asset"] == coin:
                return asset  # Returns full balance details
        return None

    def sell_crypto(self, coin, quote_coin, amount):
        trading_pair = f"{coin}{quote_coin}"  # Format as "BTCUSDT"

        order = self.client.account.new_order(
            symbol=trading_pair,  # e.g., "ETHUSDT"
            side="SELL",  # Buy order
            type="MARKET",  # Market order
            quoteOrderQty=amount  # Amount in quote currency (USDT)
        )

        return order


if __name__ == '__main__':
    mexc_data = Mexc()
    coin = 'CGPT/USDT'
    network = 'BEP20'
    asset = mexc_data.get_asset_address(coin, network)
    print(asset)