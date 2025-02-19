import re
import json

def parse_telegram_message(message):
    # Extract token and exchanges
    token_exchange_match = re.search(r"(\w+):\s+([\w-]+)→([\w-]+)", message)
    if not token_exchange_match:
        return None
    token, exchange_from, exchange_to = token_exchange_match.groups()
    print(f"Current signal for: {token}, {exchange_from}, {exchange_to}")
    # # Only process messages where either exchange is MEXC or BingX
    # if "MEXC" not in (exchange_from, exchange_to) and "BingX" not in (exchange_from, exchange_to):
    #     return None

    # Extract prices
    price_matches = re.findall(r"Цена: `([\d.]+)`", message)
    if len(price_matches) < 2:
        return None
    price_from, price_to = map(float, price_matches)

    # Extract volumes and order counts
    volume_matches = re.findall(r"Объем:\s+\*\*(.*?)\$\*\*,\s+([\d.]+M),\s+(\d+)\sордера", message)
    if len(volume_matches) < 2:
        return None


    volume_from, quantity_from, orders_from = volume_matches[0]
    volume_to, quantity_to, orders_to = volume_matches[1]

    # Convert values
    volume_from, volume_to = float(volume_from), float(volume_to)
    orders_from, orders_to = int(orders_from), int(orders_to)

    # Extract fees
    fee_matches = re.findall(r"Комиссия: спот \*\*(.*?)\$\*\* / перевод \*\*(.*?)\$\*\*", message)
    if not fee_matches:
        return None
    spot_fee, transfer_fee = map(float, fee_matches[0])

    # Extract spread
    spread_match = re.search(r"💰 Чистый спред: \*\*(.*?)\$\*\* \(\*\*(.*?)%\*\*\)", message)
    if not spread_match:
        return None
    spread_value, spread_percent = map(float, spread_match.groups())

    # Extract network
    network_match = re.search(r"Сеть:\s+(\w+)", message)
    network = network_match.group(1) if network_match else None

    # Extract lifetime
    lifetime_match = re.search(r"🕑 Время жизни: (\d+:\d+)", message)
    lifetime = lifetime_match.group(1) if lifetime_match else None

    def convert_quantity(quantity):
        if "M" in quantity:
            return float(quantity.replace("M", "")) * 1_000_000
        elif "K" in quantity:
            return float(quantity.replace("K", "")) * 1_000
        return float(quantity)

    quantity_from = convert_quantity(quantity_from)
    quantity_to = convert_quantity(quantity_to)

    # Organize into dictionary
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

# Example usage
message = """
KONAN: CoinEx→BitMart 83.8 +4.5$ (5.19%)

`KONAN`/USDT:

📗| [MEXC](https://www.coinex.com/exchange/KONAN-USDT) | [вывод](https://www.coinex.com/asset/withdraw?type=KONAN) |
Цена: `0.0000017096389` [0.00000166-`0.00000175`]
Объем: **83.8 $**, 49.04M, 4 ордера

📕| [BingX](https://www.bitmart.com/trade/ru-RU?symbol=KONAN_USDT) | [ввод](https://www.bitmart.com/asset-deposit/ru-RU) |
Цена: `0.0000018057148` [0.00000181-`0.0000018`]
Объем: **88.6 $**, 49.03M, 2 ордера

Комиссия: спот **0.34$** / перевод **0.01$** (5.40K KONAN)
Сеть: KRC20
🕑 Время жизни: 03:25
💰 Чистый спред: **4.5$** (**5.19%**)
"""

_, structured_data = parse_telegram_message(message)
print(structured_data)