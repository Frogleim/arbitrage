from bitmart.api_contract import APIContract
from exchanges import loggs

def get_futures_price(symbol):
    api_key = "YOUR_API_KEY"
    api_secret = "YOUR_SECRET_KEY"
    api_memo = "YOUR_MEMO"

    futures_client = APIContract(api_key, api_secret, api_memo)

    symbol = f"{symbol}USDT"
    try:
        response = futures_client.get_details(symbol)
        last_price = response[0]['data']['symbols'][0]['last_price']

        loggs.system_log.info(f"BitMart Latest Futures {symbol} price:", response[0]['data']['symbols'][0]['last_price'])
        return True, last_price
    except Exception as e:
        loggs.error_logs_logger.error(e)
        return False, None