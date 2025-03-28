
import time
from os import PRIO_PGRP

import requests
import hmac
from hashlib import sha256
import os
from dotenv import load_dotenv

load_dotenv()

APIURL = "https://open-api.bingx.com"


def withdraw(address, coin, amount, network):
    payload = {}
    path = '/openApi/wallets/v1/capital/withdraw/apply'
    method = "POST"
    paramsMap = {
    "address": address,
    "addressTag": "None",
    "amount": str(amount),
    "coin": coin,
    "network":  network,
    "timestamp": str(int(time.time() * 1000)),
    "walletType": "1"
}
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, urlpa, payload, api_secret, api_key):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(api_secret, urlpa))
    print(url)
    headers = {
        'X-BX-APIKEY': api_key,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    print(response.json())
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "":
     return paramsStr+"&timestamp="+str(int(time.time() * 1000))
    else:
     return paramsStr+"timestamp="+str(int(time.time() * 1000))


if __name__ == '__main__':
    withdraw(
        address="0x753bf176f4f7c56d4f19b06e09756863c28ef7c6",
        coin="POL",
        amount=6,
        network="POLYGON"

    )