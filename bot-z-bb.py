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

SOCKET = "wss://stream.binance.com:9443/ws/dogebrl@kline_1m"

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'DOGEBRL'
TRADE = 190

in_position = False

client = Client(config.API_KEY, config.API_SECRET)

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    main()

def get_data_frame():
    starttime = "1 day ago UTC"
    interval = "1m"
    bars = client.get_historical_klines(TRADE_SYMBOL, interval, "1 day ago UTC")
    #pprint.pprint(bars)

    for line in bars:
        del line[5:]

    df = pd.DataFrame(bars, columns=['date', 'open', 'high', 'low', 'close'])
    return df


def plot_graph(df):
    df = df.astype(float)
    df[['close', 'sma', 'upper', 'lower']].plot()
    plt.xlabel('Date', fontsize=18)
    plt.ylabel('Close price', fontsize=18)
    x_axis = df.index
    plt.fill_between(x_axis, df['lower'], df['upper'], color='grey', alpha=0.30)

    plt.scatter(df.index, df['buy'], color='purple', label='Buy', marker='^', alpha=1) #purple = buy
    plt.scatter(df.index, df['sell'], color='red', label='Sell', marker='v', alpha=1) #red = sell
    

    plt.show()
    

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("Sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print(e)
        return False
    
    return True


def buy_or_sell(df):
    global in_position
    buy_list = pd.to_numeric(df['buy'], downcast='float')
    sell_list = pd.to_numeric(df['sell'], downcast='float')

    for i in range(len(buy_list)):
        current_price = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
        if(float(current_price['price']) > sell_list[i]): #sell order
                if in_position == True:
                    print("Sell Sell Sell")
                                trade_fee = (TRADE/100)*0.2
            order_succeeded = order(SIDE_SELL,TRADE, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("We dont have to sell")
        elif(float(current_price['price']) < buy_list[i]): #buy order
            if in_position == False:
                print("Buy Buy Buy")
                order_succeeded = order(SIDE_BUY, TRADE, TRADE_SYMBOL)
                if order_succeeded:
                    in_position = True
                else:
                    print("We've already positioned")
        else:
            print("... do nothing ...")

def bollinger_trade_logic():
    symbol_df = get_data_frame()
    period = 20
    #small time moving average. calculate 20 MA using pandas over close price
    symbol_df['sma'] = symbol_df['close'].rolling(period).mean()
    #standard deviation
    symbol_df['std'] = symbol_df['close'].rolling(period).std()

    #calculate upper bollinger bands
    symbol_df['upper'] = symbol_df['sma'] + (2 * symbol_df['std'])

    #calculate lower bollinger bands
    symbol_df['lower'] = symbol_df['sma'] - (2 * symbol_df['std'])

    #print human time
    symbol_df.set_index('date', inplace=True)
    symbol_df.index = pd.to_datetime(symbol_df.index, unit='ms') #index set to first column = date_and_time

    close_list = pd.to_numeric(symbol_df['close'], downcast='float')
    upper_list = pd.to_numeric(symbol_df['upper'], downcast='float')
    lower_list = pd.to_numeric(symbol_df['lower'], downcast='float')

    symbol_df['buy'] = np.where(close_list < lower_list, symbol_df['close'], np.NAN)
    symbol_df['sell'] = np.where(close_list > upper_list, symbol_df['close'], np.NAN)

    with open('output.txt', 'w') as f:
        f.write(
            symbol_df.to_string()
        )
    
    plot_graph(symbol_df)

    buy_or_sell(symbol_df)

def main():
    global in_position
    bollinger_trade_logic()



ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()