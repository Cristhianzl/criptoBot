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
import talib

#EMA

client = Client(config.API_KEY, config.API_SECRET) #it takes two parameter, first one api_key and second api_secret_key, i will define that in configuration file 

SYMBOL = "ETHUSDT" #taking this as a example 
TIME_PERIOD= "15m" #taking 15 minute time period 
LIMIT = "200" # taking 200 candles as limit 
QNTY = 0.02 # we will define quantity over here 
in_position = False
qtd_execucao = 0

#Now we will write function to get data from binance to work with 
# for that we will need to import requests library to fetch data 



def place_order(order_type):
    global in_position
    try:
        #order type could be buy or sell 
        # before that , we have to initialize the binance client 
        if(order_type == "buy"):
            if(in_position == False):
                order = client.create_order(symbol=SYMBOL, side="buy",quantity=QNTY,type="MARKET") # for type i am going with market order, so whatever price at market. it will place order 
                in_position = True
                time.sleep(300)

            else:
                print("We are already positioned!")
        else:
            if(in_position == True):
                order = client.create_order(symbol=SYMBOL, side="sell", quantity=QNTY,type="MARKET") # same thing but changed side 
                in_position = False
            else:
                print("We dont have to sell!")
        print("order placed successfully!") 
        print(order)
        return

    except Exception as e:
        print(e)
        return


#now , you will need to define api_key and api-secret in the config file like this 


#function to get data from binance 
def get_data():

    try:
        url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(SYMBOL, TIME_PERIOD, LIMIT)
        res = requests.get(url) 

        return_data = []
        for each in res.json():
            return_data.append(float(each[4]))
        return np.array(return_data)

    except Exception as e:
        print(e)
        main()


#now we have function to get data from binance, now we need to calculate ema. for calculating ema, we are going to use 
# talib library, to install it do this 

#define main entry point for the script 
def main():
    global qtd_execucao
    ema_8 = None #starting with None 
    ema_21 = None #starting with None 

    #we also need to store the last variables that was the value for the ema_8 and ema_21, so we can compare
    last_ema_8 = None 
    last_ema_21 = None 

    print("started running..")
    #the script will run continously and fetch latest data from binance 
    while True:
        closing_data = get_data() #get latest closing data for the candles 
        ema_8 = talib.EMA(closing_data,8)[-1] #data and timeperiod are the two parameters that the function takes 
        ema_21 = talib.EMA(closing_data, 21)[-1] #same as the last one 

        print("Em posição: ", in_position)
        print("Market: ", SYMBOL)
        
        print("ema_8: ", round(ema_8,3))
        print("ema_21: ", round(ema_21, 3))

        if(ema_8 > ema_21 and last_ema_8): #we have to check if the value of ema_8 crossed ema_21 or not 
            if(last_ema_8 < last_ema_21): # to check if previously, it was below of ema_21 and we haven't already bought it 
                place_order("buy")

        if(ema_21 > ema_8 and last_ema_21):  #to check if ema_8 got down from top to bottom 
            if(last_ema_21 < last_ema_8): # to check if previously it was above ema_21
                place_order("sell")

        last_ema_8 = ema_8 
        last_ema_21 = ema_21

        print("Quantidade execuções: ", qtd_execucao+1)
        time.sleep(300)
        #return

        
if __name__ == "__main__":
    main()