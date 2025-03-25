import ccxt
from exchanges import loggs

# Initialize Bybit Exchange (Futures)

def check_futures_price(symbol):
    bybit = ccxt.bybit()
    bybit.load_markets()

    try:
        symbol = f"{symbol}/USDT:USDT"
        ticker = bybit.fetch_ticker(symbol)

        loggs.system_log.info(f"Bybit Latest Futures {symbol} price: {ticker['last']}")
        return True, ticker['last']
    except Exception as e:
        loggs.error_logs_logger.error(e)
        return False, None
