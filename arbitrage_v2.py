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



def get_signature(api_secret, payload):
    """Generates HMAC SHA256 signature for authentication."""
    query_string = urlencode(payload)

    signature = hmac.new(api_secret.encode("utf-8"), query_string.encode("utf-8"), sha256).hexdigest()
    print(f"🔍 Signature: {signature}")  # ✅ Debugging
    return signature


def get_signal(signal_json: Optional[dict] = None, keys: list = None) -> Tuple[bool, str]:
    """Check if coming signal is valid.

    Args:
        signal_example (dict, optional): The signal data.

    Returns:
        Tuple[bool, str]: A tuple where the first value is a boolean indicating signal validity,
                          and the second value is the exchange name.


    """

    mexc_api_key = keys[0]
    mexc_api_secret = keys[1]
    if signal_json and signal_json.get('exchange') == 'MEXC':
        mex = mexc_exchange.Mexc(mexc_api_key, mexc_api_secret)
        data = mex.check_signal(trading_pair=signal_json['symbol'], price=signal_json['price'])
        print(data)
        if data.get('is_near'):
            loggs.system_log.info("Signal is valid! Starting arbitrage")
            buy_crypto(signal_json, keys)
            return True, 'MEXC'
        else:
            return False, 'MEXC'

    return False, "UNKNOWN"


def buy_crypto(signal_data, api_keys: list):
    # is_valid, exchange = get_signal(signal_example)
    mexc = mexc_exchange.Mexc(api_keys[0], api_keys[1])
    bingx = bingx_exchange.BingX(api_keys[0], api_keys[1])
    final_quantity = float(signal_data['quantity_from']) / float(signal_data['orders_count_from'])
    spot_buying = final_quantity * float(signal_data['price_from'])
    print(f"Buying quantity: {final_quantity}")
    # if exchange == 'MEXC' and is_valid:
    for _ in range(signal_data['orders_count_from']):
        # Placing sell order in Bingx
        loggs.system_log.info("Buying crypto order")
        # Buying crypto in MEXC exchange
        order_response = mexc.buy_crypto(signal_data['token'], round(spot_buying, 1))
        loggs.system_log.info(order_response)

    mexc_exit_price = mexc.get_last_price(signal_data['token'])

    bingx_futures.open_trade(
        symbol=signal_data['token'].replace('USDT', ''),
        exit_price=float(mexc_exit_price) - 0.100,
        quantity=signal_data['quantity_from'],
        api_key=api_keys[2],
        api_secret=api_keys[3]
    )
        # loggs.system_log.info("Opening position in BingX")
        # while True:
        #     loggs.system_log.info("Monitoring position")
        #     mark_price = bingx_futures.get_market_price(symbol=signal_example['symbol'].replace('USDT', ''))
        #     loggs.system_log.info(mark_price)
        #     # Close all position with loss
        #     if float(mark_price) < float(signal_example['price'] * 0.8):
        #         bingx_futures.close_postion(signal_example['symbol'].replace('USDT', ''))
        #         mexc.sell_crypto(signal_example['symbol'], signal_example['quantity'])
        #         loggs.system_log.info("All position closed")
        #         break
        #     # Close all position with profit
        #     elif float(mark_price) >= float(mexc_exit_price):
        #         bingx_futures.close_postion(signal_example['symbol'].replace('USDT', ''))
        #         mexc.sell_crypto(signal_example['symbol'], signal_example['quantity'])
        #         loggs.system_log.info("All position closed")
        #         break


    loggs.system_log.info("Arbitrage finished")


if __name__ == '__main__':
    buy_crypto()
