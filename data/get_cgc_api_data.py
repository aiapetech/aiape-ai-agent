import os,sys
sys.path.append(os.getcwd())
from core.config import settings
import requests
import json
import time
import glob

def get_cgc_coi_list():
    api_url = settings.COINGECKO_API_BASE_URL
    api_key = settings.COINGECKO_API_KEY
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    data = []
    url = f"{api_url}/coins/list?page={i}"
    response = requests.get(url, headers=headers)
    data += response.json()
    with open('cgc_coin_list.json', 'w') as f:
        json.dump(data, f)

def get_cgc_price_api_data():
    api_url = settings.COINGECKO_API_BASE_URL
    api_key = settings.COINGECKO_API_KEY
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    data = []
    for i in range(71,100):
        url = f"{api_url}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page={i}&sparkline=false"
        response = requests.get(url, headers=headers)
        data += response.json()
        time.sleep(1)
    with open('cgc_coin_price_2.json', 'w') as f:
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
    with open('cgc_category_data.json', 'w') as f:
        json.dump(data, f)
    return data

def merge_coin_price_list():
    my_json_list = [f for f in glob.glob("/Users/jean/Work/SightSea-AI/demo/backend/cgc_coin_price_*.json")]
    data = []
    for file in my_json_list:
        with open(file) as f:
            json_data = json.load(f)
        data += json_data
    ## Initialize the mongo client
    with open('cgc_coin_price.json', 'w') as f:
        json.dump(data, f)
def get_token_category():
    categories = get_category_data()
    api_url = settings.COINGECKO_API_BASE_URL
    api_key = settings.COINGECKO_API_KEY
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    token_category = {}
    for i,item in enumerate(categories):
        category_id = item['id']
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category={category_id}&order=market_cap_desc&per_page=250&page=1&sparkline=false&locale=en"
        response = requests.get(url, headers=headers)
        token_category[category_id] = response.json()
        time.sleep(1)
    with open('cgc_coin_categories_1.json', 'w') as f:
        json.dump(token_category, f)
        
if __name__ == "__main__":
   get_token_category()