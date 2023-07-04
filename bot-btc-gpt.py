import os
from socket import close
from binance.client import Client
import pprint
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import config
import ccxt
from binance.enums import *
import websocket
import datetime as dt
import time
import requests

SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_5m"

TRADE_SYMBOL = 'BTCUSDT'
TRADE = 0.004
INTERVAL = '5m'
LIMIT = 1000

in_position = False
total_trade = 0.00
stop_loss_price = 0.00

client = Client(config.API_KEY, config.API_SECRET)

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    main()

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    global total_trade, stop_loss_price, in_position

    try:
        print("Sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity, recvWindow=60000)
        print(order)
        if(side == SIDE_BUY):
            total_trade = float(order['fills'][0]['price']) + total_trade
        else:
            total_trade = float(order['fills'][0]['price']) - total_trade
    except Exception as e:
        print(e)
        return False
    
    return True


def buy_or_sell(type):
    global in_position, total_trade

    if(type=='sell'): #sell order
        if in_position == True:
            print("Sell Sell Sell")
            order_succeeded = order(SIDE_SELL,TRADE, TRADE_SYMBOL)
            if order_succeeded:
                in_position = False
        else:
            print("We dont have to sell")
    elif(type=='buy'): #buy order
        if in_position == False:
            print("Buy Buy Buy")
            order_succeeded = order(SIDE_BUY, TRADE, TRADE_SYMBOL)
            if order_succeeded:
                in_position = True
            else:
                print("Ocorreu um erro ao executar a ordem")
                in_position = False

    else:
        print("... Sem ordem a ser executada ...")

def main():
    global in_position

    current_price = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
    price_now = float(current_price['price'])

    marketprice = f'https://api.binance.com/api/v3/klines?symbol={TRADE_SYMBOL}&interval={INTERVAL}&limit={LIMIT}'
    res = requests.get(marketprice)
    data = res.json()   

    df = pd.DataFrame(data, columns=['openTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseAssetVolume', 'takerBuyQuoteAssetVolume', 'ignore'])

    df['closeTime'] = pd.to_datetime(df['closeTime'], unit='ms')
    df.set_index('closeTime', inplace=True)

    df['MA50'] = df['close'].rolling(window=15).mean()

    # calcular os níveis de suporte e resistência
    support_level = df['MA50'].min()
    resistance_level = df['MA50'].max()
    df['WMA10'] = df['close'].rolling(window=10).apply(lambda x: wma(x, np.arange(1, 11)))

    print(f"MOEDA: {TRADE_SYMBOL}\n")

    print(f"O nível de resistência é {resistance_level:.2f}\n")

    print(f"O preço nesse momento é {price_now:.2f}\n")

    print(f"O nível de suporte é {support_level:.2f}\n")

    print(f"A WMA de 10 períodos é {df['WMA10'].iloc[-1]:.2f}\n")

    print(f"O total de trade é {total_trade:.2f}\n")

    if price_now < support_level:
        if not in_position:
            if price_now > df['WMA10'].iloc[-1]:
                print("Preço acima do nível de resistência e da WMA10. Enviando ordem de compra...")
                buy_or_sell('buy')
        else:
            print("Já há uma posição aberta. Não é possível enviar uma ordem de compra.")
    elif price_now > resistance_level:
        if in_position:
            print("Preço abaixo do nível de suporte. Enviando ordem de venda...")
            buy_or_sell('sell')
        else:
            print("Não há posição aberta. Não é possível enviar uma ordem de venda.")
    
    else:
        if in_position:
            print("Preço está entre o nível de suporte e resistência. Mantendo posição.")
        else:
            print("Preço está entre o nível de suporte e resistência. Aguardando.")
        
    time.sleep(50)  # tempo de espera para realizar a próxima iteração
    

def wma(values, weights):
    return (values * weights).sum() / weights.sum()
    
while True:
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()