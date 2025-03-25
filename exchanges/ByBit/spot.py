import ccxt
from exchanges import loggs


def check_spot_price(symbol):

    bybit = ccxt.bybit()
    bybit.load_markets()
    try:
        symbol = f"{symbol}/USDT"
        ticker = bybit.fetch_ticker(symbol)
        loggs.system_log.info(f"ByBit Latest Spot {symbol} price: {ticker['last']}")
        return True, ticker['last']
    except Exception as e:
        loggs.error_logs_logger.error(e)
        return False, None