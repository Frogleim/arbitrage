from exchanges.MEXC import mexc_exchange
from exchanges.BingX import bingx_futures, bingx_buy
from exchanges.Binance import futures as binance_futures
from exchanges.Binance import spot as binance_spot
from exchanges.KuCoin import futures as kucoin_futures
from exchanges.KuCoin import spot as kucoin_spot
from exchanges import loggs


class PositionHandler:

    def __init__(self, keys, signal_data):

        self.keys = keys
        self.signal_data = signal_data
        self.exchange_pair = {}
        self.mexc = mexc_exchange.Mexc(self.keys[0], self.keys[1])
        self.bingx_api_key = self.keys[2]
        self.bingx_api_secret = self.keys[3]
        self.binance_api_key = self.keys[4]
        self.binance_api_secret = self.keys[5]


    def check_if_signal_valid(self):

        """Check if arbitrage signal is valid."""

        self.exchange_pair = {
            'from': self.signal_data['exchange_from'],
            'to': self.signal_data['exchange_to']
        }
        print(self.exchange_pair)

        price_fetchers = {
            ('MEXC', 'BingX'): lambda: (
                self.mexc.get_last_price(self.signal_data['token']),
                bingx_futures.get_market_price(self.signal_data['token'])[1]
            ),
            ('MEXC', 'Binance'): lambda: (
                self.mexc.get_last_price(self.signal_data['token']),
                binance_futures.get_market_price(self.signal_data['token'])
            ),
            ('MEXC', 'KuCoin'): lambda: (
                self.mexc.get_last_price(self.signal_data['token']),
                kucoin_futures.check_futures_price(self.signal_data['token'])[1]
            ),

            ('BingX', 'Binance'): lambda: (
                bingx_buy.get_market_price(self.signal_data['token'], self.bingx_api_key, self.bingx_api_secret)['data'][0]['trades'][0]['price'],
                binance_futures.get_market_price(self.signal_data['token'])
            ),
            ('BingX', 'KuCoin'): lambda: (
                bingx_buy.get_market_price(self.signal_data['token'], self.bingx_api_key, self.bingx_api_secret)['data'][0]['trades'][0]['price'],
                kucoin_futures.check_futures_price(self.signal_data['token'])[1]
            ),
            ('KuCoin', 'Binance'): lambda: (
                kucoin_spot.check_spot_price(self.signal_data['token'])[1],
                binance_futures.get_market_price(self.signal_data['token'])
            ),
            ('KuCoin', 'BingX'): lambda: (
                kucoin_spot.check_spot_price(self.signal_data['token'])[1],
                bingx_buy.get_market_price(self.signal_data['token'], self.bingx_api_key, self.bingx_api_secret)[1]
            ),
        }
        fetch_prices = price_fetchers.get((self.exchange_pair['from'], self.exchange_pair['to']))
        if fetch_prices:
            price_from, price_to = fetch_prices()
            if price_from is not None and price_to is not None:
                if float(price_from) < float(price_to):
                    loggs.system_log.info(f'✅ {self.exchange_pair["from"]} price: {price_from}')
                    loggs.system_log.info(f'✅ {self.exchange_pair["to"]} price: {price_to}')
                    return True, 'Signal is valid'
                else:
                    return False, (f'Signal signal is not profitable\n{self.exchange_pair["to"]} price: {price_to} < '
                                   f'{self.exchange_pair["from"]} {price_from}')
            else:
                return False, 'Invalid price data from exchanges'

        return False, 'Signal is invalid'


    def open_spot(self):

        """Buy crypto in the spot market of the source exchange."""

        if self.exchange_pair['from'] == 'MEXC':
            final_quantity = float(self.signal_data['quantity_from']) / float(self.signal_data['orders_count_from'])
            spot_buying = final_quantity * float(self.signal_data['price_from'])
            try:
                order_response = self.mexc.buy_crypto(
                    coin=self.signal_data['token'],
                    price=float(self.signal_data['price_from']),
                    amount=round(spot_buying, 1)
                )
                if 'code' in order_response:
                    return False, 'MEXC spot opened failed'
                else:
                    return True, 'MEXC spot opened'
            except Exception as e:
                return False, f"Error buying in MEXC spot: {e}"

        elif self.exchange_pair['from'] == 'BingX':
            try:
                res = bingx_buy.buy_crypto(
                    coin=self.signal_data['token'],
                    quantity=None,
                    api_key=self.bingx_api_key,
                    api_secret=self.bingx_api_secret,
                )
                return True, 'BingX spot created'
            except Exception as e:
                return False, f"Error buying in BingX spot: {e}"

        elif self.exchange_pair['from'] == 'Binance':
            try:
                binance_spot.buy_crypto(
                    api_key=self.binance_api_key,
                    api_secret=self.binance_api_secret,
                    symbol=self.signal_data['token'],
                )
                return True, 'Binance spot created'
            except Exception as e:
                return False, f"Error buying in Binance spot: {e}"

        elif self.exchange_pair['from'] == 'KuCoin':
            try:
                kucoin_spot.buy_spot(
                    symbol=self.signal_data['token'],
                    amount=float(2),

                )
                return True, 'KuCoin spot created'
            except Exception as e:
                return False, f"Error buying in KuCoin spot: {e}"

    def open_futures_position(self):

        """Open a futures trade on the target exchange."""

        if self.exchange_pair['to'] == 'BingX':
            mexc_exit_price = self.mexc.get_last_price(self.signal_data['token'])
            is_valid, msg = bingx_futures.open_trade(
                symbol=self.signal_data['token'].replace('USDT', ''),
                exit_price=float(mexc_exit_price),
                quantity=self.signal_data['quantity_from'],
                api_key=self.bingx_api_key,
                api_secret=self.bingx_api_secret
            )
            return is_valid, 'BingX order executed successfully.'

        elif self.exchange_pair['to'] == 'Binance':
            try:
                is_valid, msg = binance_futures.open_position(
                    api_key=self.binance_api_key,
                    api_secret=self.binance_api_secret,
                    symbol=self.signal_data['token'].replace('USDT', ''),
                )
                return is_valid, 'Binance order executed successfully.'
            except Exception as e:
                return False, f"Error opening position in Binance Futures: {e}"

        elif self.exchange_pair['to'] == 'KuCoin':
            try:
                kucoin_futures.open_futures_position(
                    symbol=self.signal_data['token'].replace('USDT', ''),
                    side='sell',
                    size=2,
                    leverage=20,
                )
                return True, 'KuCoin Futures order executed successfully.'
            except Exception as e:
                return False, f"Error opening position in KuCoin Futures: {e}"

        return False, "Unknown exchange for futures trading."

    def run(self):

        """Execute the arbitrage process: validate signal, buy spot, and open futures position."""

        loggs.system_log.info("🔍 Running arbitrage strategy...")
        print("🔍 Running arbitrage strategy...")

        is_valid_signal, msg = self.check_if_signal_valid()
        if not is_valid_signal:
            loggs.system_log.warning(msg)
            return False, msg

        loggs.system_log.info("✅ Signal validated successfully!")
        print("✅ Signal validated successfully!")

        is_spot_successful, msg = self.open_spot()
        if not is_spot_successful:
            loggs.system_log.warning(msg)
            return False, msg

        loggs.system_log.info("✅ Spot buy executed successfully!")
        print("✅ Spot buy executed successfully!")

        is_futures_successful, msg = self.open_futures_position()
        if not is_futures_successful:
            loggs.system_log.warning(msg)
            return False, msg

        loggs.system_log.info("✅ Futures position opened successfully!")
        print("✅ Futures position opened successfully!")

        return True, "Arbitrage trade executed successfully!"

if __name__ == '__main__':
    keys = ['mx0vglFXKQlvzxMy6T', '4004ef44894b45cdbfba900079a4c5f2', 'K0doNDRAz90hGvBdCKeeK4S7eS5eurl6huMc9CvwyfeNHlKQBe3RUa40IFrLNZMb2Bg9t5oHN8bfrUiKOeeg', '3DetCim4QMmEofEB6LhWBerht1D4gRl4h4XmztHwZagESgfCJsa86rM4JDXKmj2ZyI1aqufhJH4Nfp1Q', 'B9Wpsjh6a3XCSYqod3XbXBeFh1ZMykOOAo6tdd2ORJVyLn2xwsIBiaS4jI1Z9kKA', 'Fqos3cwhSYos1cAldVUa3dOB2pI7R6STJ3bGbwnyB0uvfEae4ybih6CoWjcF3AlY']

    d = {'exchange_from': 'BingX', 'price_from': '0.0734786', 'quantity_from': 46430, 'orders_count_from': '3', 'exchange_to': 'KuCoin', 'price_to': '0.0750892', 'quantity_to': 46430, 'orders_count_to': '46', 'token': 'DYDX', 'futures_exchanges': ['MEXC', 'Bitget', 'XT', 'KuCoin']}
    ps = PositionHandler(signal_data=d, keys=keys)
    ps.run()