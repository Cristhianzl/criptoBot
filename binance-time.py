import time
import requests
import json
url = "https://api.binance.com/api/v1/time"
t = time.time()*1000
r = requests.get(url)

result = json.loads(r.content)

print(int(t)-result["serverTime"]) 