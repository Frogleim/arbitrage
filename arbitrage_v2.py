from typing import Tuple, Optional
import hmac
from hashlib import sha256
from exchanges import mexc_exchange, bingx_exchange, bingx_futures
from exchanges import loggs
import os
from dotenv import load_dotenv
from urllib.parse import urlencode


load_dotenv(dotenv_path='./exchanges/.env')

API_KEY = os.getenv('MEX_API_KEY')
API_SECRET = os.getenv('MEX_SECRET_KEY')
BASE_URL = "https://futures.mexc.com"


signal_example = {
    "symbol": "POLUSDT",
    "network": "POLYGON",
    "quantity": 7,
    "price": 0.3208,
    "exchange": "MEXC",
    "orders_count": 2

}

def get_signature(api_secret, payload):
    """Generates HMAC SHA256 signature for authentication."""
    query_string = urlencode(payload)

    signature = hmac.new(api_secret.encode("utf-8"), query_string.encode("utf-8"), sha256).hexdigest()
    print(f"🔍 Signature: {signature}")  # ✅ Debugging
    return signature


def get_signal(signal_example: Optional[dict] = None) -> Tuple[bool, str]:
    """Check if coming signal is valid.

    Args:
        signal_example (dict, optional): The signal data.

    Returns:
        Tuple[bool, str]: A tuple where the first value is a boolean indicating signal validity,
                          and the second value is the exchange name.
    """
    if signal_example and signal_example.get('exchange') == 'MEXC':
        mex = mexc_exchange.Mexc()
        data = mex.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        print(data)
        if data.get('is_near'):
            loggs.system_log.info("Signal is valid! Starting arbitrage")
            return True, 'MEXC'
        else:
            return False, 'MEXC'

    return False, "UNKNOWN"



def detect_exchange():
    is_valid, exchange = get_signal(signal_example)
    return is_valid, exchange



def buy_crypto( orders_count=1):
    is_valid, exchange = get_signal(signal_example)
    mexc = mexc_exchange.Mexc()
    bingx = bingx_exchange.BingX()
    final_quantity = signal_example['quantity'] / signal_example['orders_count']
    spot_buying = final_quantity * signal_example['price']
    print(f"Buying quantity: {final_quantity}")
    if exchange == 'MEXC' and is_valid:
        for _ in range(signal_example['orders_count']):
            # Placing sell order in Bingx
            loggs.system_log.info("Buying crypto order")
            # Buying crypto in MEXC exchange
            order_response = mexc.buy_crypto(signal_example['symbol'], round(spot_buying, 1))
            loggs.system_log.info(order_response)

        mexc_exit_price = mexc.get_last_price(signal_example['symbol'])

        bingx_futures.open_trade(
            symbol=signal_example['symbol'].replace('USDT', ''),
            exit_price=float(mexc_exit_price) - 0.100,
            quantity=signal_example['quantity'],
        )
        loggs.system_log.info("Opening position in BingX")
        while True:
            loggs.system_log.info("Monitoring position")
            mark_price = bingx_futures.get_market_price(symbol=signal_example['symbol'].replace('USDT', ''))
            loggs.system_log.info(mark_price)
            # Close all position with loss
            if float(mark_price) < float(signal_example['price'] * 0.8):
                bingx_futures.close_postion(signal_example['symbol'].replace('USDT', ''))
                mexc.sell_crypto(signal_example['symbol'], signal_example['quantity'])
                loggs.system_log.info("All position closed")
                break
            # Close all position with profit
            elif float(mark_price) >= float(mexc_exit_price):
                bingx_futures.close_postion(signal_example['symbol'].replace('USDT', ''))
                mexc.sell_crypto(signal_example['symbol'], signal_example['quantity'])
                loggs.system_log.info("All position closed")
                break


    loggs.system_log.info("Arbitrage finished")


if __name__ == '__main__':
    buy_crypto()
