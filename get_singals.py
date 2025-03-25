import asyncio
import json
import os
import re
from telethon import TelegramClient, events
from open_position_handler import PositionHandler
from parse_signal import clean_text
from exchanges import loggs

# Global dictionary for user sessions
user_sessions = {}
keys = []
CREDENTIALS_FILE = "settings/credentials.json"

# Telegram Bot Token
BOT_TOKEN = "7571515908:AAEcznoSzBDCal1porW7MA6ayNWfk6PnuIc"  # Replace with your bot token

# Initialize Telethon Bot Client
bot = TelegramClient("./sessions_dirs/bot_session", api_id=24465307, api_hash="a7f60a15b4f5e7f97aec85d9ea408fe1").start(
    bot_token=BOT_TOKEN
)


def load_credentials():
    """ Loads stored user credentials from file if available """
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):  # Ensure it's a dictionary
                    return data
        except json.JSONDecodeError:
            loggs.error_logs_logger.error("❌ Error: credentials.json is corrupted. Starting fresh.")
            return {}
    return {}


def save_credentials():
    """ Saves user credentials to a file """
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(user_sessions, f, indent=4)


# ✅ Load credentials at startup
user_sessions = load_credentials()
print(f"🔄 Loaded user_sessions: {user_sessions}")  # Debugging
loggs.system_log.info(f"🔄 Loaded user_sessions: {user_sessions}")  # Debugging


async def send_message_event(event, message):
    """ Sends a message in response to an event """
    await event.respond(message)

async def send_message_user(user_id, message):
    """ Sends a message to a user by their ID """
    await bot.send_message(int(user_id), message)



@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """ Handles the /start command and checks if credentials exist """
    user_id = str(event.chat_id)

    loggs.system_log.info(f"✅ User {user_id} started the bot.")  # Debugging

    if user_id in user_sessions:
        await send_message_event(event, "✅ Your credentials are already stored. Resuming arbitrage...")
        asyncio.create_task(run_telegram_client(user_id))  # ✅ Pass user_id
    else:
        await send_message_event(event, "👋 Welcome! Do you want to start arbitrage? (yes/no)")
        user_sessions[user_id] = {"step": "confirm_arbitrage"}


@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.out))
async def handle_user_input(event):
    """ Handles user messages for API credentials """
    user_id = str(event.chat_id)
    text = event.message.message.strip()

    loggs.system_log.info(f"📩 Received message from {user_id}: {text}")

    if user_id not in user_sessions:
        return

    step = user_sessions[user_id]["step"]

    if step == "confirm_arbitrage":
        if text.lower() == "yes":
            await send_message_event(event, "✅ Please enter your **API ID**:")
            user_sessions[user_id]["step"] = "api_id"
        elif text.lower() == "no":
            await send_message_event(event, "❌ Arbitrage not started. Type /start if you change your mind.")
            del user_sessions[user_id]
        else:
            await send_message_event(event, "❓ Please type 'yes' or 'no'.")

    elif step == "api_id":
        user_sessions[user_id]["api_id"] = text
        user_sessions[user_id]["step"] = "api_hash"
        await send_message_event(event, "✅ Now enter your **API Hash**:")

    elif step == "api_hash":
        user_sessions[user_id]["api_hash"] = text
        user_sessions[user_id]["step"] = "phone_number"
        await send_message_event(event, "✅ Now enter your **Phone Number** (with country code):")

    elif step == "phone_number":
        user_sessions[user_id]["phone_number"] = text
        user_sessions[user_id]["step"] = "mexc_api_key"
        await send_message_event(event, "✅ Now enter your **MEXC API Key**:")

    elif step == "mexc_api_key":
        user_sessions[user_id]["mexc_api_key"] = text
        user_sessions[user_id]["step"] = "mexc_api_secret"
        await send_message_event(event, "✅ Now enter your **MEXC API Secret Key**:")

    elif step == "mexc_api_secret":
        user_sessions[user_id]["mexc_api_secret"] = text
        user_sessions[user_id]["step"] = "bingx_api_key"
        await send_message_event(event, "✅ Now enter your **BingX API Key**:")

    elif step == "bingx_api_key":
        user_sessions[user_id]["bingx_api_key"] = text
        user_sessions[user_id]["step"] = "bingx_api_secret"
        await send_message_event(event, "✅ Now enter your **BingX API Secret Key**:")

    elif step == "bingx_api_secret":
        user_sessions[user_id]["bingx_api_secret"] = text
        user_sessions[user_id]["step"] = "binance_api_key"
        await send_message_event(event, "✅ Now enter your **Binance API Key**:")

    elif step == "binance_api_key":
        user_sessions[user_id]["binance_api_key"] = text
        user_sessions[user_id]["step"] = "binance_api_secret"
        await send_message_event(event, "✅ Now enter your **Binance API Secret Key**:")

    elif step == "binance_api_secret":
        user_sessions[user_id]["binance_api_secret"] = text
        user_sessions[user_id]["step"] = "listening"

        # ✅ Save credentials to file
        save_credentials()

        await send_message_event(event, "✅ All credentials saved! Bot is now listening for signals...")
        asyncio.create_task(run_telegram_client(user_id))


async def run_telegram_client(user_id):
    """ Runs the Telegram client for the user """
    user_data = user_sessions.get(user_id, {})

    if not user_data:
        print(f"❌ Error: No data found for user {user_id}. Skipping...")
        return

    required_keys = ["api_id", "api_hash", "phone_number", "mexc_api_key", "mexc_api_secret", "bingx_api_key", "bingx_api_secret"]
    for key in required_keys:
        if key not in user_data:
            print(f"❌ Error: Missing '{key}' for user {user_id}. Skipping...")
            return

    api_id = int(user_data["api_id"])
    api_hash = user_data["api_hash"]
    phone_number = user_data["phone_number"]
    mexc_api_key = user_data["mexc_api_key"]
    mexc_api_secret = user_data["mexc_api_secret"]
    bingx_api_key = user_data["bingx_api_key"]
    bingx_api_secret = user_data["bingx_api_secret"]
    binance_api_key = user_data["binance_api_key"]
    binance_api_secret = user_data["binance_api_secret"]

    keys.extend([mexc_api_key, mexc_api_secret, bingx_api_key, bingx_api_secret, binance_api_key, binance_api_secret])
    client = TelegramClient(f"user_session_{user_id}", api_id, api_hash)

    @client.on(events.NewMessage(chats='@ArbitrageSmartBot'))
    async def handler(event):
        """ Processes incoming trading signals """
        is_valid_signal, data = clean_text(event.message.text)
        loggs.system_log.info(f'Signal is valid: {is_valid_signal}')
        if is_valid_signal:
            message = (f"📢 Signal received:\n"
                       f"🔹 Token: {data['token']}\n"
                       f"📈 From: {data['exchange_from']} at {data['price_from']}\n"
                       f"📉 To: {data['exchange_to']} at {data['price_to']}")
            await send_message_user(user_id, message)

            await send_message_user(user_id, "Received signal! Buying crypto")
            position_handler = PositionHandler(
                keys=keys,
                signal_data=data,
            )
            is_finished, msg = position_handler.run()
            if is_finished:
                await send_message_user(user_id, f"✅ All orders completed successfully!\n{msg}")
            else:

                await send_message_user(user_id, f"❌ Arbitrage doesnt complete!\n{msg}")

    await client.start(phone_number)
    await send_message_user(user_id, "✅ Listening for signals from @ArbitrageSmartBot...")
    await client.run_until_disconnected()





if __name__ == "__main__":
    loggs.system_log.info("✅ Telegram bot is running...")
    bot.run_until_disconnected()
#

