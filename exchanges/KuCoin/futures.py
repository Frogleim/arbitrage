from kucoin_futures.client import Market, Trade
from exchanges import loggs

FUTURES_API_KEY = "67dfafe66fb8e00001f0bae4"
FUTURES_API_SECRET = "0fb4c639-13ee-4358-b2b7-f9c3f6c9809e"
FUTURES_API_PASSPHRASE = "Gor199521"

futures_client = Trade(FUTURES_API_KEY, FUTURES_API_SECRET, FUTURES_API_PASSPHRASE)


def check_futures_price(symbol):
    client = Market()

    symbol = f"{symbol}USDTM"

    # Get the latest price
    try:
        ticker = client.get_ticker(symbol)
        loggs.system_log.info(f"KuCoin Latest {symbol} price: {ticker['price']}")
        return True, ticker['price']
    except Exception as e:
        loggs.error_logs_logger.error(e)
        return False, None


def open_futures_position(symbol: str, side: str, size: float, leverage: int = 20):
    try:
        # Set leverage
        # futures_client.change_cross_user_leverage(f'{symbol}USDTM', leverage)

        # Place a market order (long or short)
        order = futures_client.create_market_order(f'{symbol}USDTM', 'sell', size=2, lever=leverage)
        print(f"✅ Futures {side.upper()} Order Placed: {order}")
        return order['orderId']
    except Exception as e:
        print(f"❌ Error in Futures Order: {e}")



if __name__ == '__main__':
    FUTURES_SYMBOL = "MAVIA"  # MATIC/USDT Perpetual Contract
    POSITION_SIZE = 1  # Size in contracts (adjust as needed)
    LEVERAGE = 5  # Set leverage

    # Open a long (buy) position
    open_futures_position(FUTURES_SYMBOL, "buy", POSITION_SIZE, LEVERAGE)