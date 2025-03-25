from binance.client import Client
from binance.enums import *
from  exchanges import loggs
import math



def adjust_quantity(client, symbol, quantity):
    """Ensure quantity matches Binance LOT_SIZE rules"""
    exchange_info = client.get_symbol_info(symbol)
    lot_size_filter = next(f for f in exchange_info["filters"] if f["filterType"] == "LOT_SIZE")

    min_qty = float(lot_size_filter["minQty"])  # 0.1
    step_size = float(lot_size_filter["stepSize"])  # 0.1

    # Ensure quantity is at least minQty
    if quantity < min_qty:
        quantity = min_qty

    # Round down to nearest valid step size (must be a multiple of stepSize)
    quantity = math.floor(quantity / step_size) * step_size

    return quantity


def get_spot_price(symbol):
    client = Client()

    ticker = client.get_symbol_ticker(symbol=f"{symbol}USDT")
    return float(ticker["price"])

def buy_crypto(api_key, api_secret, symbol):
    loggs.system_log.info(f'Buying {symbol} in Binance Spot account')

    try:
        client = Client(api_key, api_secret)

        # Check if trading pair exists
        exchange_info = client.get_symbol_info(f"{symbol}USDT")
        if not exchange_info:
            loggs.error_logs_logger.error(f"Trading pair {symbol}USDT not found on Binance.")
            return

        # Fetch price
        ticker = client.get_symbol_ticker(symbol=f"{symbol}USDT")
        if not isinstance(ticker, dict) or "price" not in ticker:
            loggs.error_logs_logger.error(f"Invalid ticker response: {ticker}")
            return

        btc_price = float(ticker["price"])
        quantity = round(2 / btc_price)  # Initial calculation

        # Adjust quantity based on Binance LOT_SIZE rules
        quantity = adjust_quantity(client, f"{symbol}USDT", quantity)

        # If quantity is still too small, log an error
        if quantity < 0.1:
            loggs.error_logs_logger.error(f"Calculated quantity ({quantity}) is below min LOT_SIZE.")
            return

        # Place market buy order
        order = client.order_market_buy(
            symbol=f"{symbol}USDT",
            quantity=quantity
        )
        loggs.system_log.info(order)

    except Exception as e:
        loggs.error_logs_logger.error(f'Error while buying {symbol} in Binance Spot: {str(e)}')


if __name__ == '__main__':
    api_key = 'B9Wpsjh6a3XCSYqod3XbXBeFh1ZMykOOAo6tdd2ORJVyLn2xwsIBiaS4jI1Z9kKA'
    api_secret = 'Fqos3cwhSYos1cAldVUa3dOB2pI7R6STJ3bGbwnyB0uvfEae4ybih6CoWjcF3AlY'
    symbol = 'OP'
    buy_crypto(
        api_key=api_key,
        api_secret=api_secret,
        symbol=symbol
    )


