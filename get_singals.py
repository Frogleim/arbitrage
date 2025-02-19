from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from telethon import TelegramClient, events
import asyncio
import json
from arbitrage_v2 import get_signal
import re


api_id = '24465307'
api_hash = 'a7f60a15b4f5e7f97aec85d9ea408fe1'
phone_number = '+37495663938'
app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

def parse_telegram_message(message):
    token_exchange_match = re.search(r"(\w+):\s+([\w-]+)→([\w-]+)", message)
    if not token_exchange_match:
        return False, None

    token, exchange_from, exchange_to = token_exchange_match.groups()
    socketio.emit('log', {'message': f"Current signal for: {token}, {exchange_from}, {exchange_to}"})

    if "MEXC" not in (exchange_from) and "BingX" not in (exchange_from):
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

@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    keys = []
    api_id = request.form['api_id']
    api_hash = request.form['api_hash']
    phone_number = request.form['phone_number']
    mexc_api_key = request.form['mexc_api_key']
    mexc_api_secret = request.form['mexc_api_secret']
    bingx_api_key = request.form['bingx_api_key']
    bingx_api_secret = request.form['bingx_api_secret']
    keys.append([mexc_api_key, mexc_api_secret, bingx_api_key, bingx_api_secret])
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_telegram_client(api_id, api_hash, phone_number, keys))

    return jsonify({"status": "Listening for messages..."})

async def run_telegram_client(api_id, api_hash, phone_number, keys):
    client = TelegramClient('session_name', api_id, api_hash)

    @client.on(events.NewMessage(chats='@ArbitrageSmartBot'))
    async def handler(event):
        is_valid_signal, json_signal = parse_telegram_message(event.message.text)
        if is_valid_signal:
            signal_data = json.loads(json_signal)
            if signal_data['exchange_from'] == 'MEXC' and signal_data['exchange_to'] == 'BingX':
                get_signal(signal_data, keys)
                socketio.emit('log', {'message': f"Signal received: {signal_data}"})


    await client.start(phone_number)
    socketio.emit('log', {'message': "Telegram client started."})
    await client.run_until_disconnected()

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)