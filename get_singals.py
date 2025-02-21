import asyncio
import json
import re
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SendMessageRequest
from arbitrage_v2 import buy_crypto

# Dictionary to store user sessions
user_sessions = {}
keys = []
# Telegram Bot Token
BOT_TOKEN = "7571515908:AAEcznoSzBDCal1porW7MA6ayNWfk6PnuIc"  # Replace with your bot token from @BotFather

# Initialize Telethon Bot Client
bot = TelegramClient("./sessions_dirs/bot_session", api_id=24465307, api_hash="a7f60a15b4f5e7f97aec85d9ea408fe1").start(
    bot_token=BOT_TOKEN)


async def send_message(user_id, message):
    """ Sends a message to the user via the bot """
    await bot(SendMessageRequest(user_id, message))


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """ Handles the /start command, asks whether to start arbitrage """
    user_id = event.chat_id
    print(f"✅ User {user_id} started the bot.")  # Debugging
    await send_message(user_id, "👋 Welcome! Do you want to start arbitrage? (yes/no)")
    user_sessions[user_id] = {"step": "confirm_arbitrage"}


@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.out))  # ✅ Only process user messages
async def handle_user_input(event):
    """ Handles user messages for API credentials """
    user_id = event.chat_id
    text = event.message.message.strip().lower()

    print(f"📩 Received message from {user_id}: {text}")  # ✅ Debugging

    # ✅ Ensure user is in session before proceeding
    if user_id not in user_sessions:
        print(f"⚠️ Ignoring message from {user_id}, user session not found.")  # ✅ Debugging
        return

    step = user_sessions[user_id]["step"]

    if step == "confirm_arbitrage":
        if text == "yes":
            await send_message(user_id, "✅ Please enter your **API ID**:")
            user_sessions[user_id]["step"] = "api_id"
        elif text == "no":
            await send_message(user_id, "❌ Arbitrage not started. Type /start if you change your mind.")
            del user_sessions[user_id]
        else:
            await send_message(user_id, "❓ Please type 'yes' or 'no'.")

    elif step == "api_id":
        user_sessions[user_id]["api_id"] = text
        user_sessions[user_id]["step"] = "api_hash"
        await send_message(user_id, "✅ Now enter your **API Hash**:")

    elif step == "api_hash":
        user_sessions[user_id]["api_hash"] = text
        user_sessions[user_id]["step"] = "phone_number"
        await send_message(user_id, "✅ Now enter your **Phone Number** (with country code):")

    elif step == "phone_number":
        user_sessions[user_id]["phone_number"] = text
        user_sessions[user_id]["step"] = "mexc_api_key"
        await send_message(user_id, "✅ Now enter your **MEXC API Key**:")

    elif step == "mexc_api_key":
        user_sessions[user_id]["mexc_api_key"] = text
        user_sessions[user_id]["step"] = "mexc_api_secret"
        await send_message(user_id, "✅ Now enter your **MEXC API Secret Key**:")

    elif step == "mexc_api_secret":
        user_sessions[user_id]["mexc_api_secret"] = text
        user_sessions[user_id]["step"] = "bingx_api_key"
        await send_message(user_id, "✅ Now enter your **BingX API Key**:")

    elif step == "bingx_api_key":
        user_sessions[user_id]["bingx_api_key"] = text
        user_sessions[user_id]["step"] = "bingx_api_secret"
        await send_message(user_id, "✅ Now enter your **BingX API Secret Key**:")

    elif step == "bingx_api_secret":
        user_sessions[user_id]["bingx_api_secret"] = text
        await send_message(user_id, "✅ All credentials saved! Bot is now listening for signals...")
        user_sessions[user_id]["step"] = "listening"
        asyncio.create_task(run_telegram_client(user_id))


async def run_telegram_client(user_id):
    """ Runs the Telegram client for the user """
    user_data = user_sessions[user_id]
    api_id = int(user_data["api_id"])
    api_hash = user_data["api_hash"]
    phone_number = user_data["phone_number"]
    mexc_api_key = user_data["mexc_api_key"]
    mexc_api_secret = user_data["mexc_api_secret"]
    bingx_api_key = user_data["bingx_api_key"]
    bingx_api_secret = user_data["bingx_api_secret"]

    keys.extend([mexc_api_key, mexc_api_secret, bingx_api_key, bingx_api_secret])
    client = TelegramClient(f"user_session_{user_id}", api_id, api_hash)

    @client.on(events.NewMessage(chats='@ArbitrageSmartBot'))
    async def handler(event):
        """ Processes incoming trading signals """
        print(event.message.text)
        is_valid_signal, data = parse_telegram_message(event.message.text)
        print(data)

        if is_valid_signal:
            message = (f"📢 Signal received:\n"
                       f"🔹 Token: {data['token']}\n"
                       f"📈 From: {data['exchange_from']} at {data['price_from']}\n"
                       f"📉 To: {data['exchange_to']} at {data['price_to']}")

            await send_message(user_id, message)
            if data['exchange_from'] == "MEXC" and data['exchange_to'] == "BingX":
                await client.send_message(user_id, "Recived signal! Buying crypto")
            # Ensure buy_crypto is awaited and its result is checked
                is_finished = await buy_crypto(data, keys)

                if is_finished:
                    await send_message(user_id, "✅ Buy order completed successfully!")
                    # Continue with further processing if needed

    await client.start(phone_number)
    await send_message(user_id, "✅ Listening for signals from @ArbitrageSmartBot...")
    await client.run_until_disconnected()


def parse_telegram_message(message):
    token_exchange_match = re.search(r"(\w+):\s+([\w-]+)→([\w-]+)", message)
    if not token_exchange_match:
        return False, None

    token, exchange_from, exchange_to = token_exchange_match.groups()

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


if __name__ == "__main__":
    print("✅ Telegram bot is running...")
    bot.run_until_disconnected()