from kucoin.client import Market, Trade
from exchanges import loggs


SPOT_API_KEY = "67dfafe66fb8e00001f0bae4"
SPOT_API_SECRET = "0fb4c639-13ee-4358-b2b7-f9c3f6c9809e"
SPOT_API_PASSPHRASE = "Gor199521"
spot_client = Trade(SPOT_API_KEY, SPOT_API_SECRET, SPOT_API_PASSPHRASE)

def check_spot_price(symbol):
    client = Market()

    symbol = f"{symbol}-USDT"
    try:
        ticker = client.get_ticker(symbol)
        loggs.system_log.info(f"KuCoin Latest {symbol} spot price: {ticker['price']}")
        return True, ticker['price']
    except Exception as e:
        loggs.error_logs_logger.error(e)
        return False, None


def buy_spot(symbol: str, amount: float):
    try:
        order = spot_client.create_market_order(f'{symbol}-USDT', 'buy', funds=2)
        print(f"✅ Spot Buy Order Placed: {order}")
        return order['orderId']
    except Exception as e:
        print(f"❌ Error in Spot Buy: {e}")


def buy_spot_limit(symbol: str, funds: float = 2.0):
    # Get the current price of the symbol
    _, price = check_spot_price(symbol)
    print(price)
    # Calculate the amount of crypto you can buy for the specified funds
    amount = float(funds) / float(price)
    print(round(amount, 2))
    try:
        order = spot_client.create_limit_order(
            f'{symbol}-USDT',  # Symbol pair
            'buy',  # Action (buy/sell)
            size=round(amount, 2),  # Amount of the asset to buy
            price=price  # Limit price
        )
        print(f"✅ Limit Buy Order Placed: {order}")
        return order['orderId']
    except Exception as e:
        print(f"❌ Error in Limit Buy: {e}")

if __name__ == "__main__":
    SPOT_SYMBOL = "ACE"  # MATIC Spot Pair
    SPOT_BUY_AMOUNT = 2  # Buy $2 worth of MATIC

    # Buy MATIC on Spot
    buy_spot(SPOT_SYMBOL, SPOT_BUY_AMOUNT)