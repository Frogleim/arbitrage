from os import PRIO_PGRP

from exchanges import mexc_exchange, bingx_exchange

signal_example = {
    "symbol": "ETHUSDT",
    "network": "BEP20",
    "quantity": 1,
    "price": 2608,
    "exchange": "BINGX"
}
def get_signal():
    if signal_example['exchange'] == 'MEXC':
        mex = mexc_exchange.Mexc()
        data = mex.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        print(data)
        if data['is_near']:
            print("Signal is valid! Starting arbitrage")
            return True, 'MEXC'
        else:
            return False, 'MEXC'

    elif signal_example['exchange'] == 'BINGX':
        bingx = bingx_exchange.BingX()
        data = bingx.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        if data['is_near']:
            print("Signal is valid! Starting arbitrage")
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
        contract = next((item['contractAddress'] for item in addr if item['network'] == signal_example['network']), None)

        print(f'BINGX {coin} address: {contract}')

        print(f"Buying {signal_example['symbol']} with quantity {signal_example['quantity']} on BINGX")
        # order = mex.buy_crypto(
        #     coin=signal_example['symbol'],
        #     amount=signal_example['quantity']
        # )
        # print(order)
        print(f'Sending crypto to BING address')
        bingx.sell_crypto()
        print('Finishing')

    elif is_valid and exchange == 'BINGX':
        addr = mex.get_asset_address(
            coin=coin,
            network=signal_example['network']
        )
        print(addr)
        print(f"Buying {signal_example['symbol']} with quantity {signal_example['quantity']} on MEXC")





if __name__ == '__main__':
    # get_signal()
    start_arbitrage()