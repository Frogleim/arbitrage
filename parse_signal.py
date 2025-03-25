import re
import json
from exchanges import loggs

def convert_abbreviation(value):
    """ Converts abbreviated numbers like '2.05K' into normal numbers (e.g., 2050) """
    match = re.match(r'([\d.]+)([KMB]?)', value)
    if not match:
        return value
    num, suffix = match.groups()
    num = float(num)

    if suffix == "K":
        num *= 1_000
    elif suffix == "M":
        num *= 1_000_000
    elif suffix == "B":
        num *= 1_000_000_000

    return int(num) if num.is_integer() else num


def contains_numbered_symbol(text):
    return "№" in text


def remove_price_ranges(data_list):
    """ Removes number ranges like 0.0733-0.0735 """
    return [item for item in data_list if not re.match(r'^\d+(\.\d+)?-\d+(\.\d+)?$', item)]


def extract_futures_exchanges(text):
    """ Extracts exchange names from the '✅Фьючерсы' line """
    futures_match = re.search(r'✅Фьючерсы: (.+)', text)
    if futures_match:
        exchanges = re.findall(r'\[([^\]]+)\]', futures_match.group(1))
        return exchanges
    return []


def clean_text(text):

    is_contain = contains_numbered_symbol(text)
    print("Text contains '№' symbol:", is_contain)

    futures_exchanges = extract_futures_exchanges(text)
    print("Futures Exchanges:", futures_exchanges)

    text = re.sub(r'[^\w\s.,:|$()/\[\]-]', '', text, flags=re.UNICODE)

    lines = text.strip().split("\n")
    if len(lines) > 2:
        text = "\n".join(lines[1:-1])

    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'№\d+', '', text)
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    text = re.sub(r'\b[А-Яа-яЁё]+\b', '', text)
    text = re.sub(r'[|,|/]', '', text)
    text = re.sub(r'[()]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[:$]', '', text)

    l_data = text.split()
    l_data = remove_price_ranges(l_data)


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
            "token": l_data[0].replace('USDT', ''),
            "futures_exchanges": futures_exchanges
        }
    else:
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
            "token": l_data[0].replace('USDT', ''),
            "futures_exchanges": futures_exchanges
        }

    loggs.debug_log.debug(d)
    try:
        with open("settings/settings.json", "r") as f:
            data = json.load(f)
            print(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        loggs.system_log.error(f"Settings file error: {e}")
        return False, None

    matched = [exchange for exchange in d['futures_exchanges'] if exchange in data['exchanges_to'] and exchange != d['exchange_from']]
    if not matched:  # Fix: Check if list is empty instead of None
        return False, None

    d['exchange_to'] = matched[0]  # Assign first match
    return True, d


if __name__ == '__main__':
    with open("settings/settings.json", "r") as f:
        data = json.load(f)
        print(data)
    print(data['exchanges_to'])