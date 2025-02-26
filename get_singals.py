import asyncio
import json
import os
import re
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SendMessageRequest
from arbitrage_v2 import buy_crypto

# Global dictionary for user sessions
user_sessions = {}
keys = []
CREDENTIALS_FILE = "credentials.json"

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
            print("❌ Error: credentials.json is corrupted. Starting fresh.")
            return {}
    return {}


def save_credentials():
    """ Saves user credentials to a file """
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(user_sessions, f, indent=4)


# ✅ Load credentials at startup
user_sessions = load_credentials()
print(f"🔄 Loaded user_sessions: {user_sessions}")  # Debugging


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

    print(f"✅ User {user_id} started the bot.")  # Debugging

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

    print(f"📩 Received message from {user_id}: {text}")

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

    keys.extend([mexc_api_key, mexc_api_secret, bingx_api_key, bingx_api_secret])
    print(keys)
    client = TelegramClient(f"user_session_{user_id}", api_id, api_hash)

    @client.on(events.NewMessage(chats='@ArbitrageSmartBot'))
    async def handler(event):
        """ Processes incoming trading signals """
        is_valid_signal, data = clean_text(event.message.text)

        print('Signal is valid:', is_valid_signal)
        if is_valid_signal:
            message = (f"📢 Signal received:\n"
                       f"🔹 Token: {data['token']}\n"
                       f"📈 From: {data['exchange_from']} at {data['price_from']}\n"
                       f"📉 To: {data['exchange_to']} at {data['price_to']}")
            await send_message_user(user_id, message)

            if data['exchange_from'] == "MEXC" and data['exchange_to'] == "BingX":
                await send_message_user(user_id, "Received signal! Buying crypto")
                is_finished, msg = buy_crypto(data, keys)

                if is_finished:
                    await send_message_user(user_id, f"✅ All orders completed successfully!\n{msg}")
                else:

                    await send_message_user(user_id, f"❌ Arbitrage doesnt complete!\n{msg}")

    await client.start(phone_number)
    await send_message_user(user_id, "✅ Listening for signals from @ArbitrageSmartBot...")
    await client.run_until_disconnected()


def remove_price_ranges(data_list):
    """ Removes elements that match the pattern of a number range (e.g., 0.03788-0.0379) """
    return [item for item in data_list if not re.match(r'^\d+(\.\d+)?-\d+(\.\d+)?$', item)]


def contains_numbered_symbol(text):
    if "№" in text:
        return True
    else:
        return False


def convert_abbreviation(value):
    """ Converts abbreviated numbers like '2.05K' into normal numbers (e.g., 2050) """
    match = re.match(r'([\d.]+)([KMB]?)', value)  # Match number and optional suffix
    if not match:
        return value  # Return unchanged if no match

    num, suffix = match.groups()
    num = float(num)  # Convert to float

    # Multiply based on suffix
    if suffix == "K":
        num *= 1_000
    elif suffix == "M":
        num *= 1_000_000
    elif suffix == "B":
        num *= 1_000_000_000

    return int(num) if num.is_integer() else num

def clean_text(text):
    is_contain = contains_numbered_symbol(text)
    print('Text contains:', is_contain)
    text = re.sub(r'[^\w\s.,:|$()/\[\]-]', '', text, flags=re.UNICODE)

    lines = text.strip().split("\n")
    if len(lines) > 2:  # Ensure there are at least 3 lines to remove first and last
        text = "\n".join(lines[1:-1])
    # Remove all URLs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'№\d+', '', text)

    # Remove square brackets but keep the text inside them
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)

    # Remove words that contain Cyrillic characters (if needed)
    text = re.sub(r'\b[А-Яа-яЁё]+\b', '', text)
    text = re.sub(r'[|,|/]', '', text)
    text = re.sub(r'[()]', '', text)

    # Remove extra spaces left from removed content
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove specific unwanted characters like ':' and '$'
    text = re.sub(r'[:$]', '', text)
    l_data = text.split()
    l_data = remove_price_ranges(l_data)

    print(l_data)
    if is_contain:
        quantity_from = convert_abbreviation(l_data[5])
        quantity_to = convert_abbreviation(l_data[10])
        d = {
        "exchange_from": l_data[2],
        "price_from": l_data[3],
        "quantity_from": quantity_from,
        'orders_count_from': l_data[6],
        "exchange_to": l_data[7],
        "price_to": l_data[8],
        "quantity_to": quantity_to,
        "orders_count_to": l_data[11],
        "token": l_data[0],

        }



        print(d)
        if d['exchange_from'] != "MEXC" or d['exchange_to'] != "BingX":
            print("❌ Error: Exchange mismatch (Expected MEXC -> BingX)")
            return False, None
        return True, d

    elif not is_contain:
        quantity_from = convert_abbreviation(l_data[4])
        quantity_to = convert_abbreviation(l_data[9])
        d = {
            "exchange_from": l_data[1],
            "price_from": l_data[2],
            "quantity_from": quantity_from,
            'orders_count_from': l_data[5],
            "exchange_to": l_data[6],
            "price_to": l_data[7],
            "quantity_to": quantity_to,
            "orders_count_to": l_data[11],
            "token": l_data[0],

        }

        print(d)

        if d['exchange_from'] != "MEXC" or d['exchange_to'] != "BingX":
            print("❌ Error: Exchange mismatch (Expected MEXC -> BingX)")
            return False, None
        return True, d
    else:
        return False, None






if __name__ == "__main__":
    print("✅ Telegram bot is running...")
    bot.run_until_disconnected()
#     message = """
#   ✅GPU: MEXC→BingX 297.6 +2.1$ (0.67%)
#
# GPU/USDT: №610
#
# 📗| MEXC | вывод |
# Цена: 0.4225
# Объем: 297.6 $, 704.57, 1 ордер
#
# 📕| BingX | ввод |
# Цена: 0.428002 [0.43-0.428]
# Объем: 300.3 $, 701.57, 2 ордера
#
# Комиссия: спот 0.6$ / перевод 1.27$ (3 GPU)
# Сеть: ERC20
# 🟢 3-13 минут (5 подт. ~ 1 мин)
# 🕑 Время жизни: 00:01
# 💰 Чистый спред: 2.1$ (0.67%)
# 👍Контракты совпадают
#
# ✅Фьючерсы: MEXC
#     """
#     is_valid, data = parse_telegram_message(message)
#     print(data)