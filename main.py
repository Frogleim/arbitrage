import asyncio
import json
import re
from telethon import TelegramClient, events
from arbitrage_v2 import get_signal

# Telegram API credentials
api_id = '24465307'
api_hash = 'a7f60a15b4f5e7f97aec85d9ea408fe1'
phone_number = '+37495663938'

# Initialize Telegram Client
client = TelegramClient('session_name', api_id, api_hash)

def parse_telegram_message(message):
    """Parses incoming Telegram messages for trading signals."""
    token_exchange_match = re.search(r"(\w+):\s+([\w-]+)→([\w-]+)", message)
    if not token_exchange_match:
        return False, None

    token, exchange_from, exchange_to = token_exchange_match.groups()

    if "MEXC" not in exchange_from and "BingX" not in exchange_from:
        return False, None

    price_matches = re.findall(r"Цена: `([\d.]+)`", message)
    if len(price_matches) < 2:
        return False, None
    price_from, price_to = map(float, price_matches)

    volume_matches = re.findall(r"Объем:\s+\*\*(.*?)\$\*\*,\s+([\d.]+[MK]),\s+(\d+)\sордера", message)
    if len(volume_matches) < 2:
        return False, None

    volume_from, quantity_from, orders_from = volume_matches[0]
    volume_to, quantity_to, orders_to = volume_matches[1]

    volume_from, volume_to = float(volume_from), float(volume_to)
    orders_from, orders_to = int(orders_from), int(orders_to)

    def convert_quantity(quantity):
        if "M" in quantity:
            return float(quantity.replace("M", "")) * 1_000_000
        elif "K" in quantity:
            return float(quantity.replace("K", "")) * 1_000
        return float(quantity)

    quantity_from = convert_quantity(quantity_from)
    quantity_to = convert_quantity(quantity_to)

    fee_matches = re.findall(r"Комиссия: спот \*\*(.*?)\$\*\* / перевод \*\*(.*?)\$\*\*", message)
    if not fee_matches:
        return False, None
    spot_fee, transfer_fee = map(float, fee_matches[0])

    spread_match = re.search(r"💰 Чистый спред: \*\*(.*?)\$\*\* \(\*\*(.*?)%\*\*\)", message)
    if not spread_match:
        return False, None
    spread_value, spread_percent = map(float, spread_match.groups())

    network_match = re.search(r"Сеть:\s+(\w+)", message)
    network = network_match.group(1) if network_match else None

    lifetime_match = re.search(r"🕑 Время жизни: (\d+:\d+)", message)
    lifetime = lifetime_match.group(1) if lifetime_match else None

    data = {
        "token": token,
        "exchange_from": exchange_from,
        "exchange_to": exchange_to,
        "price_from": price_from,
        "price_to": price_to,
        "volume_from": volume_from,
        "volume_to": volume_to,
        "orders_count_from": orders_from,
        "orders_count_to": orders_to,
        "quantity_from": quantity_from,
        "quantity_to": quantity_to,
        "spot_fee": spot_fee,
        "transfer_fee": transfer_fee,
        "network": network,
        "spread_value": spread_value,
        "spread_percent": spread_percent,
        "lifetime": lifetime
    }

    return True, json.dumps(data, indent=4, ensure_ascii=False)

async def run_telegram_client(keys):
    """Runs the Telegram client and listens for messages."""
    @client.on(events.NewMessage(chats='@blumcrypto'))
    async def handler(event):
        is_valid_signal, json_signal = parse_telegram_message(event.message.text)
        print(is_valid_signal)
        # if is_valid_signal:
        #     signal_data = json.loads(json_signal)
        #     if signal_data['exchange_from'] == 'MEXC' and signal_data['exchange_to'] == 'BingX':
        #         get_signal(signal_data, keys)
        #         print(f"Signal received: {signal_data}")

    await client.start(phone_number)
    print("Telegram client started.")
    await client.run_until_disconnected()

# Run the client
if __name__ == '__main__':
    keys = []  # Define API keys if needed
    asyncio.run(run_telegram_client(keys))