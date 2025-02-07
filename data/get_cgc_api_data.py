import os,sys
sys.path.append(os.getcwd())
from core.config import settings
import requests
import json
import time

def get_cgc_price_api_data():
    api_url = settings.COINGECKO_API_BASE_URL
    api_key = settings.COINGECKO_API_KEY
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    data = []
    for i in range(1,80):
        url = f"{api_url}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page={i}&sparkline=false"
        response = requests.get(url, headers=headers)
        data += response.json()
        time.sleep(1)
    with open('cgc_data_1.json', 'w') as f:
        json.dump(data, f)

def get_category_data():
    api_url = settings.COINGECKO_API_BASE_URL
    api_key = settings.COINGECKO_API_KEY
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    data = []
    url = f"{api_url}/coins/categories"
    response = requests.get(url, headers=headers)
    data += response.json()
    with open('cgc_category_data_1.json', 'w') as f:
        json.dump(data, f)
if __name__ == "__main__":
    get_category_data()
    