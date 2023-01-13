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

SOCKET = "wss://stream.binance.com:9443/ws/lunausdt@kline_1m"

LENGTH_BB = 30
WIDTH_BB = 3
TRADE_SYMBOL = 'LUNAUSDT'
TRADE = 1.5
FEE = 0.002
TRADE_SELL = 2.09


in_position = False
total_trade = 0.00

client = Client(config.API_KEY, config.API_SECRET)

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    main()

def bollingerband(symbol, width, intervalunit, length):
        start_str = '100 minutes ago UTC'
        interval_data = '1m'

        #montar data frame das bandas de bollinger
        D = pd.DataFrame(
            client.get_historical_klines(symbol=symbol, start_str=start_str, interval=interval_data)
        )
        D.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'is_best_match']
        D['open_date_time'] = [dt.datetime.fromtimestamp(x/1000) for x in D.open_time]
        D['symbol'] = symbol
        D = D[['symbol', 'open_date_time', 'open', 'high', 'low', 'close', 'volume', 'num_trades', 'taker_base_vol', 'taker_quote_vol']]
        df = D.set_index("open_date_time")
        df['close'] = df['close'].astype(float)
        df = df['close']
        df1 = df.resample(intervalunit).agg({
            "close":"last"
        })
        unit = width
        band1 = unit * np.std(df1['close'][len(df1) - length:len(df1)])
        bb_center = np.mean(df1['close'][len(df1) - length:len(df1)])
        band_high = bb_center + band1
        band_low = bb_center - band1

        return band_high, bb_center, band_low

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    global total_trade
    try:
        print("Sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
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
    global in_position
    global total_trade
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
                print("We've already positioned")
    else:
        print("... Sem ordem a ser executada ...")

def main():
    global in_position
    bb_1m = bollingerband(TRADE_SYMBOL, WIDTH_BB, '1T', LENGTH_BB)

    current_price = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
    price_now = float(current_price['price'])

    marketprice = 'https://api.binance.com/api/v1/ticker/24hr?symbol='+TRADE_SYMBOL
    res = requests.get(marketprice)
    data = res.json()

    print("Variation: ", data['priceChangePercent'])
    print("Coin: ", TRADE_SYMBOL)
    print("BB: ", round(bb_1m[0],2), round(bb_1m[2],2))
    print("Preço: ", price_now)
    print("Total de lucro: ", round(total_trade,4))
    print("Em posição: ", in_position)

    #configurar as ordens
#if variation > 0:
    if price_now > bb_1m[0]:
        buy_or_sell('sell')
    elif price_now < bb_1m[2]:
        buy_or_sell('buy')
    else:
        print("Sem ordens a serem executadas.")
#else:
    # if in_position:
    #     buy_or_sell('sell')
    #     print("Reversão de tendência, saindo da posição!")
    # else:
    #     print("Tendencia de baixa. Não faça nada.")


while True:
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()