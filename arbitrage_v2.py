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
    mexc = mexc_exchange.Mexc(api_keys[0], api_keys[1])
    final_quantity = float(signal_data['quantity_from']) / float(signal_data['orders_count_from'])
    spot_buying = final_quantity * float(signal_data['price_from'])
    loggs.system_log.info(f"Buying quantity: {final_quantity}")
    # for _ in range(signal_data['orders_count_from']):
    loggs.system_log.info("Buying crypto order")
    try:
        order_response = mexc.buy_crypto(
            coin=signal_data['token'],
            price=float(signal_data['price_from']),
            amount=round(spot_buying, 1))
        loggs.system_log.info(order_response)
        loggs.system_log.info(f"Coin {signal_data['token']} Bought in MEXC")
    except Exception as e:
        loggs.error_logs_logger.info(e)
        return False, f"Error while trying to buy crypto in MEXC spot: {e}"

    mexc_exit_price = mexc.get_last_price(signal_data['token'])

    is_valid, msg = bingx_futures.open_trade(
        symbol=signal_data['token'].replace('USDT', ''),
        exit_price=float(mexc_exit_price),
        quantity=signal_data['quantity_from'],
        api_key=api_keys[2],
        api_secret=api_keys[3]
    )
    if is_valid:
        loggs.system_log.info(f"Position opened in BingX: {mexc_exit_price}\nMEXC spot order completed successfully!")
        return True, msg
    else:
        return False, msg



if __name__ == '__main__':
    buy_crypto()
