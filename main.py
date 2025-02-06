import time

from exchanges import mexc_exchange, bingx_exchange, loggs
from decimal import Decimal, ROUND_DOWN

signal_example = {
    "symbol": "POLUSDT",
    "network": "POL",
    "quantity": 3,
    "price": 0.336,
    "exchange": "MEXC"
}


def round_amount(amount, decimals=2):
    return Decimal(amount).quantize(Decimal(f'1.{"0" * decimals}'), rounding=ROUND_DOWN)


def get_signal():
    if signal_example['exchange'] == 'MEXC':
        mex = mexc_exchange.Mexc()
        data = mex.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        if data['is_near']:
            loggs.system_log.info("Signal is valid! Starting arbitrage")
            return True, 'MEXC'
        else:
            return False, 'MEXC'

    elif signal_example['exchange'] == 'BINGX':
        bingx = bingx_exchange.BingX()
        data = bingx.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        if data['is_near']:
            loggs.system_log.info("Signal is valid! Starting arbitrage")
            return True, 'BINGX'
        else:
            return False, 'BINGX'

def start_arbitrage():
    mex = mexc_exchange.Mexc()
    coin =  signal_example['symbol'][:-4]  # Remove last 4 characters ("USDT")
    bingx = bingx_exchange.BingX()
    is_valid, exchange = get_signal()
    if is_valid and exchange == 'MEXC':
        addr = bingx.get_asset_address(
            coin=coin,
            network=signal_example['network']
        )

        loggs.system_log.info(f'BINGX {coin} address: {addr}')
        price_data = mex.client.market.ticker_price(symbol=signal_example['symbol'])
        matic_price = float(price_data[0]['price'])  # Convert to float
        required_usdt = round_amount(matic_price * signal_example['quantity'], decimals=2)
        usdt_balance = mex.check_balance("USDT")  # Fetch balance details
        available_usdt = float(usdt_balance["free"]) if usdt_balance else 0

        loggs.system_log.info(f"Buying {signal_example['symbol']} with quantity {signal_example['quantity']} on MEXC")
        if available_usdt >= required_usdt:
            # Step 4: Buy MATIC with the available USDT
            order_response = mex.buy_crypto(signal_example['symbol'], required_usdt)
            loggs.system_log.info("Order placed:", order_response)
        else:
            loggs.system_log.info("Insufficient USDT balance. Required:", required_usdt, "Available:", available_usdt)
        # print(order)
        time.sleep(15)
        loggs.system_log.info('Waiting 15 seconds...')
        loggs.system_log.info(f'Sending crypto to BING address')
        mex.withdraw(
            amount=required_usdt,
            coin=coin,
            network=signal_example['network'],
            address=addr
        )
        bingx.sell_crypto()
        loggs.system_log.info('Finishing')

    elif is_valid and exchange == 'BINGX':
        addr = mex.get_asset_address(
            coin=coin,
            network=signal_example['network']
        )

        loggs.system_log.info(f"Buying {signal_example['symbol']} with quantity {signal_example['quantity']} on MEXC")





if __name__ == '__main__':
    # get_signal()
    start_arbitrage()