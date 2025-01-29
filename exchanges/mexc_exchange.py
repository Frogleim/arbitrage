from mexc_api.spot import Spot
import os
from dotenv import load_dotenv

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
                print("Found asset:", asset)  # Debugging to see the matched coin

                # Loop through available networks
                for net in asset["networkList"]:
                    if network.lower() in net["network"].lower():  # Partial match
                        return net["contract"]  # Return the contract address

        return None  # If coin or network is not found

    def check_signal(self, trading_pair):
        price_data = self.client.market.ticker_price(symbol=trading_pair)
        return price_data

    def withdraw(self, amount, coin, network, address):
        withdraw_amount = self.client.wallet.withdraw(
            asset=coin,
            network=network,
            address=address,
            amount=amount
        )
        return withdraw_amount



if __name__ == '__main__':
    mexc_data = Mexc()
    coin = 'CGPT/USDT'
    network = 'BEP20'
    asset = mexc_data.get_asset_address(coin, network)
    print(asset)