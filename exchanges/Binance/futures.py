from binance.client import Client
from exchanges import loggs
from binance.enums import *
import math


def get_market_price(symbol):
    client = Client()

    price = client.futures_mark_price(symbol=f'{symbol}USDT')

    return price['markPrice']


def get_min_quantity(symbol):
    """Fetch minimum order quantity for a given symbol on Binance Futures."""
    client = Client()
    exchange_info = client.futures_exchange_info()


    # Fetch symbol info
    symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == f"{symbol}USDT"), None)
    if not symbol_info:
        return f"Symbol {symbol} not found."

    # Fetch filters
    min_notional = None
    step_size = None

    for filt in symbol_info['filters']:
        if filt['filterType'] == "MIN_NOTIONAL":
            min_notional = float(filt['notional'])
            print(min_notional)
        if filt['filterType'] == "LOT_SIZE":
            step_size = float(filt['stepSize'])

    if not min_notional or not step_size:
        return f"Missing filter data for {symbol}."

    # Fetch market price
    price = float(client.futures_mark_price(symbol=f"{symbol}USDT")['markPrice'])

    # Calculate minimum quantity
    min_qty = min_notional / price
    min_qty = math.ceil(min_qty / step_size) * step_size  # Adjust to step size

    return {
        "symbol": symbol,
        "min_quantity": min_qty,
        "step_size": step_size,
        "min_notional": min_notional
    }



def open_position(api_key, api_secret, symbol):

    client = Client(
        api_key=api_key,
        api_secret=api_secret,
    )
    client.futures_change_leverage(
        symbol=f'{symbol}USDT',
        leverage=20
    )
    loggs.debug_log.debug(f'Position side for opening position: SELL')
    price = client.futures_mark_price(
        symbol=f"{symbol}USDT",
    )
    data = get_min_quantity('KAS')
    loggs.system_log.info(f'Coin data in Binance Futures: {data}')

    try:
        order = client.futures_create_order(
            symbol=f'{symbol}USDT',
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=data['min_quantity'],

        )
        print(order)
        return True, f'Futures Position Opened with price'
    except Exception as e:
        loggs.error_logs_logger.error(f"Error while closing position: {e}")
        return False, f"Error while opening position: {e}"


if __name__ == '__main__':
    res = open_position(
        api_key="B9Wpsjh6a3XCSYqod3XbXBeFh1ZMykOOAo6tdd2ORJVyLn2xwsIBiaS4jI1Z9kKA",
        api_secret="Fqos3cwhSYos1cAldVUa3dOB2pI7R6STJ3bGbwnyB0uvfEae4ybih6CoWjcF3AlY",
        symbol="KAS"
    )
    print(res)
    # data = get_min_quantity('KAS')
    # print(data)