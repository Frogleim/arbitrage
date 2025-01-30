from exchanges import mexc_exchange

signal_example = {
    "symbol": "ETHUSDT",
    "network": "BEP20",
    "quantity": 1,
    "price": 3270
}
def get_signal():
    mex = mexc_exchange.Mexc()
    data = mex.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
    print(data)
    if data['is_near']:
        print("Signal is valid! Starting arbitrage")

        return True
    return False


def start_arbitrage():
    mex = mexc_exchange.Mexc()
    coin =  signal_example['symbol'][:-4]  # Remove last 4 characters ("USDT")

    is_valid = get_signal()
    if is_valid:
        addr = mex.get_asset_address(
            coin=coin,
            network=signal_example['network']
        )
        print(addr)
        # order = mex.buy_crypto(
        #     coin=signal_example['symbol'],
        #     amount=signal_example['quantity']
        # )
        # print(order)
        print(f"Buying {signal_example['symbol']} with quantity {signal_example['quantity']} on MEXC")





if __name__ == '__main__':
    # get_signal()
    start_arbitrage()