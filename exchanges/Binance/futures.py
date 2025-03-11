from binance.client import Client
import loggs
from binance.enums import *
import math


def open_position(api_key, api_secret, symbol):

    client = Client(
        api_key=api_key,
        api_secret=api_secret,
    )
    client.futures_change_leverage(
        symbol=f'{symbol}USDT',
        leverage=30
    )
    loggs.debug_log.debug(f'Position side for opening position: SELL')
    price = client.futures_mark_price(
        symbol="ADAUSDT",
    )
    exchange_info = client.futures_exchange_info()
    for symbol in exchange_info['symbols']:
        if symbol['symbol'] == 'ADAUSDT':
            for filt in symbol['filters']:
                if filt['filterType'] == 'PRICE_FILTER':
                    tick_size = float(filt['tickSize'])
                    print(f"Min Price: {filt['minPrice']}, Tick Size: {filt['tickSize']}")
    adjusted_price = math.floor(float(price['markPrice']) / float(tick_size)) * float(tick_size)
    try:
        client.futures_create_order(
            symbol=f'{symbol}USDT',
            side=SIDE_SELL,
            type=ORDER_TYPE_LIMIT,
            price=round(adjusted_price, 5),
            quantity=7,
            timeInForce="GTC"

        )
        loggs.system_log.info(f'Position opened with side: SELL')
    except Exception as e:
        loggs.error_logs_logger.error(f"Error while closing position: {e}")


if __name__ == '__main__':
    pass