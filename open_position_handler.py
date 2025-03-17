from exchanges.MEXC import mexc_exchange
from exchanges.BingX import bingx_futures, bingx_buy
from exchanges.Binance import futures, spot
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

    def check_coins_exist(self):
        """Check if a token exists on the target exchange (BingX or Binance Futures)."""
        if self.signal_data['exchange_to'] == 'BingX':
            is_exist_bingx, _ = bingx_futures.get_market_price(self.signal_data['token'])
            return is_exist_bingx
        elif self.signal_data['exchange_to'] == 'Binance':
            is_exist_binance = futures.get_market_price(self.signal_data['token'])
            return is_exist_binance
        return False  # If the exchange is unknown

    def check_if_signal_valid(self):
        """Check if arbitrage signal is valid."""
        self.exchange_pair = {
            'from': self.signal_data['exchange_from'],
            'to': self.signal_data['exchange_to']
        }

        if self.exchange_pair['from'] == 'MEXC' and self.exchange_pair['to'] == 'BingX':
            mexc_last_price = self.mexc.get_last_price(self.signal_data['token'])
            _, bingx_last_price = bingx_futures.get_market_price(self.signal_data['token'])
            loggs.system_log.info(f"mexc_last_price={mexc_last_price} signal mexc last_price={self.signal_data['price_from']} "
                                  f"bingx_last_price={bingx_last_price} signal bingx_signal_price={self.signal_data['price_to']}")
            return True, 'Signal is valid'
   

        elif self.exchange_pair['from'] == 'MEXC' and self.exchange_pair['to'] == 'Binance':
            mexc_last_price = self.mexc.get_last_price(self.signal_data['token'])
            binance_price = futures.get_market_price(self.signal_data['token'])
            loggs.system_log.info(
                f"mexc_last_price={mexc_last_price} signal mexc last_price={self.signal_data['price_from']} "
                f"binance_last_price={binance_price} signal binance_signal_price={self.signal_data['price_to']}")
            
            
            return True, 'Signal is valid'


        elif self.exchange_pair['from'] == 'BingX' and self.exchange_pair['to'] == 'Binance':
            _, bingx_last_price = bingx_buy.get_market_price(self.signal_data['token'], self.bingx_api_key, self.bingx_api_secret)
            binance_price  = futures.get_market_price(self.signal_data['token'])
            loggs.system_log.info(
                f"bingx_last_price={bingx_last_price} signal mexc last_price={self.signal_data['price_from']} "
                f"binance_last_price={binance_price} signal binance_signal_price={self.signal_data['price_to']}")
            return True, 'Signal is valid'

        else:
            return False, 'Signal is invalid'


    def open_spot(self):
        """Buy crypto in the spot market of the source exchange."""
        is_valid = self.check_coins_exist()
        if not is_valid:
            return False, 'Coin does not exist on the target exchange.'

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
                    return False, order_response['msg']
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
            except Exception as e:
                return False, f"Error buying in BingX spot: {e}"

        elif self.exchange_pair['from'] == 'Binance':
            try:
                spot.buy_crypto(
                    api_key=self.binance_api_key,
                    api_secret=self.binance_api_secret,
                    symbol=self.signal_data['token'],
                )
            except Exception as e:
                return False, f"Error buying in Binance spot: {e}"

        return True, "Spot order executed successfully."

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
            return is_valid, msg

        elif self.exchange_pair['to'] == 'Binance':
            try:
                is_valid, msg = futures.open_position(
                    api_key=self.binance_api_key,
                    api_secret=self.binance_api_secret,
                    symbol=self.signal_data['token'].replace('USDT', ''),
                )
                return is_valid, msg
            except Exception as e:
                return False, f"Error opening position in Binance Futures: {e}"

        return False, "Unknown exchange for futures trading."

    def run(self):
        """Execute the arbitrage process: validate signal, buy spot, and open futures position."""
        loggs.system_log.info("🔍 Running arbitrage strategy...")
        print("🔍 Running arbitrage strategy...")

        # Step 1: Check if signal is valid
        is_valid_signal, msg = self.check_if_signal_valid()
        if not is_valid_signal:
            loggs.system_log.warning(msg)
            return False, msg

        loggs.system_log.info("✅ Signal validated successfully!")
        print("✅ Signal validated successfully!")

        # Step 2: Execute spot buy
        is_spot_successful, msg = self.open_spot()
        if not is_spot_successful:
            loggs.system_log.warning(msg)
            return False, msg

        loggs.system_log.info("✅ Spot buy executed successfully!")
        print("✅ Spot buy executed successfully!")

        # Step 3: Open futures position
        is_futures_successful, msg = self.open_futures_position()
        if not is_futures_successful:
            loggs.system_log.warning(msg)
            return False, msg

        loggs.system_log.info("✅ Futures position opened successfully!")
        print("✅ Futures position opened successfully!")

        # self.exchange_pair = {}
        return True, "Arbitrage trade executed successfully!"
