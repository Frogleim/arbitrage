from bitmart.api_spot import APISpot
from exchanges import loggs


def get_spot_price(symbol):
# Initialize BitMart Spot API
    spot_client = APISpot()

    # Fetch spot ticker (e.g., BTC/USDT)
    try:
        symbol = "BTC_USDT"
        response = spot_client.get_v3_ticker(symbol)

        loggs.system_log.info(f"BitMart Latest Spot {symbol} price:", response[0]['data']['last'])
        return True, response[0]['data']['last']
    except Exception as e:
        loggs.error_logs_logger.error(f"Error getting Spot {symbol} price: {e}")
        return False, None