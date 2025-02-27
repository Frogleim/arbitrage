import ccxt

mexc = ccxt.mexc(config={
    'apiKey': "mx0vglFXKQlvzxMy6T",
    'secret': "4004ef44894b45cdbfba900079a4c5f2",
    'enableRateLimit': True
})



def mexc_withdraw(token, amount, address, network):
    print(amount, token, 'to', address)
    try:
        mexc.withdraw(code=token, amount=amount, address=address, params={"network": network})
        print("Withdraw successful.\n")
    except Exception as e:
        print(e)



mexc_withdraw(
    token='ETH',
    amount=1,
    address='0x1e269d187c5cc1acc1e25c8eb2938b4690f28038',
    network='ERPC20'
)
