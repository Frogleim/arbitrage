import time
from exchanges import mexc_exchange, bingx_exchange, loggs
from decimal import Decimal, ROUND_DOWN

signal_example = {
    "symbol": "POLUSDT",
    "network": "POLYGON",
    "quantity": 10,
    "price": 0.3183,
    "exchange": "BINGX"
}

def convert_network_name(network: str) -> str:
    if network.upper() == "POLYGON":
        return "Polygon(MATIC)"
    return network  # Return unchanged if not POLYGON


def round_amount(amount, decimals=2):
    return Decimal(amount).quantize(Decimal(f'1.{"0" * decimals}'), rounding=ROUND_DOWN)


def get_signal():
    if signal_example['exchange'] == 'MEXC':
        mex = mexc_exchange.Mexc()
        data = mex.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        print(data)
        if data['is_near']:
            loggs.system_log.info("Signal is valid! Starting arbitrage")
            return True, 'MEXC'
        else:
            return False, 'MEXC'

    elif signal_example['exchange'] == 'BINGX':
        bingx = bingx_exchange.BingX()
        data = bingx.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
        print(data)

        if data['is_near']:
            loggs.system_log.info("Signal is valid! Starting arbitrage")
            return True, 'BINGX'
        else:
            return False, 'BINGX'


def start_arbitrage():
    mex = mexc_exchange.Mexc()
    bingx = bingx_exchange.BingX()

    coin = signal_example['symbol'].replace('USDT', '')  # Extract base coin name
    is_valid, exchange = get_signal()

    if is_valid:
        if exchange == 'MEXC':
            # ✅ Get deposit address on BingX
            addr = bingx.get_asset_address(
                coin=coin,
                network=signal_example['network']
            )
            loggs.system_log.info(f'BINGX {coin} address: {addr}')

            # ✅ Fetch MATIC/USDT market price from MEXC
            price_data = mex.check_signal(trading_pair=signal_example['symbol'], price=signal_example['price'])
            matic_price = float(price_data["market_price"])
            required_usdt = round_amount(matic_price * signal_example['quantity'], decimals=2)

            # ✅ Check balance before buying
            usdt_balance = mex.check_balance("USDT")
            available_usdt = float(usdt_balance["free"]) if usdt_balance else 0

            loggs.system_log.info(
                f"Buying {signal_example['symbol']} with quantity {signal_example['quantity']} on MEXC")
            if available_usdt >= required_usdt:
                order_response = mex.buy_crypto(signal_example['symbol'], signal_example['quantity'])
                loggs.system_log.info(f"Order placed: {order_response}")
            else:
                loggs.system_log.info(
                    f"Insufficient USDT balance. Required: {required_usdt}, Available: {available_usdt}")
                return

            loggs.system_log.info('Waiting 15 seconds before withdrawal...')
            time.sleep(4)

            # ✅ Withdraw crypto to BingX
            try:
                network = convert_network_name(signal_example['network'])
                print(f'Symbol: {coin.replace("USDT", "")} Network: {network}')
                is_withdraw = mex.withdraw(
                    amount=required_usdt,
                    coin=coin.replace('USDT', ''),
                    network=network,
                    address=addr
                )
                loggs.system_log.info(f'Withdraw status: {is_withdraw}')

                if is_withdraw:
                    loggs.system_log.info('Waiting for transaction confirmation...')
                    time.sleep(5 * 60)  # 4 minutes delay
                    data = bingx.sell_crypto(symbol=signal_example['symbol'], quantity=signal_example['quantity'])
                    print(data)
                    loggs.system_log.info('Arbitrage trade completed!')
                else:
                    loggs.system_log.info('Withdrawal was unsuccessful')
            except Exception as e:
                loggs.system_log.error(e)

        elif exchange == 'BINGX':
            # ✅ Convert network name if necessary
            network = convert_network_name(signal_example['network'])

            # ✅ Get deposit address on MEXC
            addr = mex.get_asset_address(
                coin=coin.replace('USDT', '_USDT'),
                network=network
            )
            loggs.system_log.info(f'MEXC {coin} address: {addr}')

            # ✅ Buy on BingX
            res = bingx.buy_crypto(signal_example['symbol'].replace('USDT', ''), signal_example['quantity'])
            print(res)
            loggs.system_log.info(f"Bought {signal_example['symbol']} on BINGX")

            loggs.system_log.info("Waiting 15 seconds before withdrawal...")
            time.sleep(4)

            # ✅ Withdraw from BingX to MEXC
            try:
                is_withdraw = bingx.withdraw(
                    coin=coin,
                    address=addr,
                    amount=signal_example['quantity'],
                    network=signal_example['network']
                )
                loggs.system_log.info(f'Withdraw status: {is_withdraw}')

                if is_withdraw:
                    loggs.system_log.info('Waiting for transaction confirmation...')
                    time.sleep(6 * 60)  # 6 minutes delay
                    mex.sell_crypto(signal_example['symbol'], signal_example['quantity'])
                    loggs.system_log.info('Arbitrage trade completed!')
                else:
                    loggs.system_log.info('Withdrawal was unsuccessful')
            except Exception as e:
                loggs.system_log.error(e)



if __name__ == '__main__':
    # get_signal()
    start_arbitrage()