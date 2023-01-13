import websockets
import asyncio
import pandas as pd
import json


SOCKET = "wss://stream.binance.com:9443/ws/bnbbrl@kline_1m"

stream = \
websockets.connect(SOCKET)

async def recever():
    async with stream as receiver:
        data = await receiver.recv()
        df = createframe(data)
        print(df)

def createframe(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:, ['s','E', 'c']]
    df.columns = ['symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df


