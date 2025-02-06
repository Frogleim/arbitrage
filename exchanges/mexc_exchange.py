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
        wallet_assets = self.client.wallet.info()
        base_coin = coin.split("/")[0]  # Extracts "CGPT" from "CGPT/USDT"
        for asset in wallet_assets:
            if asset["coin"] == base_coin:
                for net in asset["networkList"]:
                    if network.lower() in net["network"].lower():
                        return net["contract"]  # Return the contract address
        return None

    def check_signal(self, trading_pair, price, threshold=0.02):
        price_data = self.client.market.ticker_price(symbol=trading_pair)
        market_price = float(price_data[0]['price'])  # Convert to float
        diff = abs(price - market_price) / market_price
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

    def buy_crypto(self, coin, amount):
        order = self.client.account.new_order(
            symbol=coin,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            quote_order_quantity=amount
        )
        return order

    def check_balance(self, coin):
        balances = self.client.account.get_account_info()["balances"]
        print(balances)
        for asset in balances:
            if asset["asset"] == coin:
                return asset  # Returns full balance details
        return None

    def sell_crypto(self, coin, quote_coin, amount):
        trading_pair = f"{coin}{quote_coin}"  # Format as "BTCUSDT"
        order = self.client.account.new_order(
            symbol=trading_pair,
            side="SELL",
            type="MARKET",
            quoteOrderQty=amount
        )
        return order

    def get_assets_by_address(self, target_address):
        wallet_assets = self.client.wallet.info()
        matching_assets = []
        for asset in wallet_assets:
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


    mexc_data = Mexc()

    # Step 1: Get current market price of MATIC/USDT
    price_data = mexc_data.client.market.ticker_price(symbol="POLUSDT")
    matic_price = float(price_data[0]['price'])  # Convert to float

    # Step 2: Calculate required USDT to buy 1 MATIC
    required_usdt = round_amount(matic_price * 3.5, decimals=2)
    print(required_usdt)
    # Step 3: Check USDT balance
    usdt_balance = mexc_data.check_balance("USDT")  # Fetch balance details
    available_usdt = float(usdt_balance["free"]) if usdt_balance else 0

    if available_usdt >= required_usdt:
        # Step 4: Buy MATIC with the available USDT
        order_response = mexc_data.buy_crypto("POLUSDT", required_usdt)
        print("Order placed:", order_response)
    else:
        print("Insufficient USDT balance. Required:", required_usdt, "Available:", available_usdt)