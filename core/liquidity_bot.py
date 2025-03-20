import requests
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dotenv
import time
import asyncio
from apify_client import ApifyClient
import json
from bs4 import BeautifulSoup
import websocket
from websocket import create_connection
import pandas as pd
from core.telegram_bot import TelegramBot
from moralis import evm_api
from datetime import datetime
from mongodb import init_mongo



dotenv.load_dotenv()
CWD = os.getcwd()

BURNED_ADDRESSES = ["0x000000000000000000000000000000000000dEaD"]
def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


class LiquidityBot:
    def __init__(self):
        self.dex_screener_base_url = "https://api.dexscreener.com/"
        #self.moralis_base_url = os.get
        self.cmc_headers = {
            "accept":"application/json",
            "X-CMC_PRO_API_KEY":os.getenv("CMC_DEXSCAN_API_KEY")
        }
        self.apify_client = ApifyClient(token=os.getenv("APIFY_TOKEN"))
        self.cgc_headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": os.getenv('COINGECKO_API_KEY')
        }
        self.telegram_bot = TelegramBot()
        self.moralis_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjgxZTY1Yjk4LTc5OGMtNDZlOS04Yjg2LTYzNTc5ZTgzMzBiMSIsIm9yZ0lkIjoiNDIyMDcxIiwidXNlcklkIjoiNDM0MDgxIiwidHlwZUlkIjoiZTU2MGEwNmQtMWUzYS00OTY3LWFlNTMtMjc3YzBkMjgxMmM2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3MzQ4MzY1NzgsImV4cCI6NDg5MDU5NjU3OH0.HRZOSN3-iN5hcWbIot444zcoY5_BIfD5322cuZWDCUE'
        self.moralis_headers = {
            "Accept": "application/json",
            "X-API-Key": self.moralis_api_key
        }
        self.mongo_client = init_mongo()
    
    def get_new_pairs_cmc(self):
        params = {
            "pageSize":50,
            "page":1,
            "age":2,
            "platformId":14,
            "liquidity":0,
            "volume":0
        }
        url = "https://api.coinmarketcap.com/dexer/v3/dexer/new-pair-list"
        response = requests.get(url,params=params)
        total = response.json()['data']['total']
        total_pages = int(total)//50
        data=  response.json()['data']['pageList']
        if total_pages == 0:
            return response.json()['data']['pageList']
        else:
             for page in range(1,total_pages+1):
                params["page"] = page
                response = requests.get(url,params=params)
                data += response.json()['data']['pageList']
                
                time.sleep(0.5)
        res = [
            {"cmc_data":record} for record in data
        ]
        return res
    
    def get_new_pool_cgc(self,network="bsc"):
        params = {
            "network":'bsc'
        }
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/new_pools"
        response = requests.get(url,headers=self.cgc_headers)

        return response
    def get_token_holder_list(self,token_address):
        url = f"https://api.dexscreener.com/token/{token_address}/holders"
        response = requests.get(url)
        return response.json()
    
    def get_new_pairs_dextool_ws(self):
        headers = {
            "sec-websocket-key":"rOrinjpxeVlx53Q4h/LjSA==",
            "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "sec-websocket-extensions":"permessage-deflate; client_no_context_takeover; server_no_context_takeover",
            "host":"ws.dextools.io",
            "origin":"https://www.dextools.io",
            "pragma":"no-cache",
            "upgrade":"websocket",
            "uwebsockets":"20",
        }
        ws = create_connection("wss://ws.dextools.io",header = headers)
        ws.send('{jsonrpc: "2.0", method: "subscribe", params: {chain: "bsc", channel: "bsc:pools"}, id: 1}')
        ws.send('{jsonrpc: "2.0", method: "subscribe", params: {chain: "bsc", channel: "bsc:common"}, id: 2}')
        while True:
            result = ws.recv()
            print(result)
        return data    
    
    def get_trending_bsc_pools(self):
        url = "https://pro-api.coingecko.com/api/v3/onchain/networks/bsc/trending_pools?duration=1h"
        headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": os.getenv("COINGECKO_API_KEY")
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def get_new_pairs_cmc_pro(self,network="bsc",limit=2000):
        url = "https://pro-api.coinmarketcap.com/v4/dex/spot-pairs/latest"
        params = {
            "network_slug":network,
            'liquidity_max':100,
            "aux":"security_scan,pool_created,percent_pooled_base_asset,pool_base_asset,holders",
            "sort_dir":"asc",
        }
        response = requests.get(url,params=params,headers=self.cmc_headers)
        cmc_data = []
        total_pages = int(limit/50)+1
        for i in range(1,total_pages):
            params["scroll_id"] = i*50
            response = requests.get(url,params=params,headers=self.cmc_headers)
            cmc_data += response.json()['data']
        with open(f"{CWD}/cmc_token_data.json","w") as f:
            json.dump(cmc_data,f)
        return cmc_data
    
    def get_new_pairs_cgc_pro(self,network="bsc",limit=2000,pool_created_hour_max="1h"):
        #url = "https://pro-api.coingecko.com/api/v3/onchain/pools/megafilter"
        
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/new_pools"
        self.cgc_data = []
        total_pages = int(limit/20)+1
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        for page in range(1,total_pages):
            params = {
            "networks":network,
            "page":page,
            "sort":"pool_created_at_desc",
            "pool_created_hour_max":pool_created_hour_max,
        }
            response = requests.get(url, headers=self.cgc_headers,params=params)
            if len(response.json()['data']) == 0 :
                break
            last_pool = response.json()['data'][-1]
            pool_created_at = datetime.strptime(last_pool['attributes']['pool_created_at'], date_format)
            time_diff = datetime.now().utcnow() - pool_created_at
            
            
            self.cgc_data+= response.json()['data']
            if time_diff.seconds > int(pool_created_hour_max[:-1]) * 60 * 60:
                break
        with open(f"{CWD}/cgc_token_data.json","w") as f:
            json.dump(self.cgc_data,f)
        return self.cgc_data
    
    def filter_image_url(self,tokens):
        filter_data = []
        for token in tokens:
            network =token['cmc_data']['platform']['name'].lower()
            address = token['cmc_data']['baseToken']['address']
            url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{address}"
            response = requests.get(url, headers=self.cgc_headers).json()
            token['cgc_data'] = response['data']
            if token['cgc_data']['attributes'].get('image_url'):
                filter_data.append(token)
        return filter_data
    
    def get_token_price_data(self,network,contract_address):
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{contract_address}"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()

    def get_pool_data_cmc(self,cgc_tokens):
        tokens = []
        new_address = [pool['attributes']['address'] for pool in cgc_latest_pools]
        cmc_tokens = []
        for batch_address in batch(new_address, 20):
            batch_address = ",".join(batch_address)
            params = {
                "contract_address":batch_address,
                "network_slug":"bsc",
                "aux":"pool_created,percent_pooled_base_asset,num_transactions_24h,pool_base_asset,pool_quote_asset,24h_volume_quote_asset,total_supply_quote_asset,total_supply_base_asset,holders,buy_tax,sell_tax,security_scan,24h_no_of_buys,24h_no_of_sells,24h_buy_volume,24h_sell_volume"
            }
            url = "https://pro-api.coinmarketcap.com/v4/dex/pairs/quotes/latest"
            response = requests.get(url, params=params,headers=self.cmc_headers).json()
            cmc_tokens += response['data']
            time.sleep(0.3)
        for cgc_token in cgc_tokens:
            for record in cmc_tokens:
                if record['contract_address'] in cgc_token['id']:
                    cmc_pool_name = record['name']
                    cmc_base_asset =  cmc_pool_name.split("/")[0]
                    cmc_quote_asset = cmc_pool_name.split("/")[1]
                    cgc_pool_name = cgc_token['attributes']['name']
                    cgc_base_asset = cgc_pool_name.split("/")[0].strip()
                    cgc_quote_asset = cgc_pool_name.split("/")[1].strip()
                    if cgc_base_asset.lower() == cmc_base_asset.lower():
                        is_base_asset = True
                    else:
                        is_base_asset = False
                    token = {
                        "cmc_data":record,
                        "cgc_data":cgc_token,
                        "is_base_asset":is_base_asset
                    }
                    tokens.append(token)
            
        # with open(f"{CWD}/latest_token_data.json","w") as f:
        #     json.dump(tokens,f)
        return tokens
    def filter_security_tokens(self,data):
        filtered_data = []
        key_failed = []
        for record in data:
            if record['contract_address'] in ['0x88449fb49fb3fac195cb7731e2fd1780fb33d77a']:
                pass
            passed = True
            item = record['security_scan'][0]
            if item['aggregated']['contract_verified'] != True:
                continue
            if item['aggregated']['honeypot'] == True:
                continue
            third_party = item['third_party']
            false_keys = [
                'proxy',
                'owner_address',
                'owner_change_balance',
                'hidden_owner',
                'self_destruct',
                'external_call',
                'gas_abuse',
                'slippage_modifiable'
            ]
            true_keys = [
                'open_source',
                'trust_list'   
            ]
            true_retricted_keys = [
                'airdrop_scam',
                'mintable',
                'blacklisted',
                'whitelist',
                'can_take_back_ownership'
            ]
            false_retricted_keys = [
                'open_source'
            ]
            for key,value in third_party.items():
                if key in true_retricted_keys and value == True:
                    passed = False
                    key_failed.append(key)
                    continue
                if key in false_retricted_keys and value != True:
                    passed = False
                    key_failed.append(key)
                    continue
                if key in false_keys and value == True :
                    passed = False
                    key_failed.append(key)
                    continue
                if key in true_keys and value == False:
                    passed = False
                    key_failed.append(key)
                    continue
            if passed:
                filtered_data.append(record)
        return filtered_data
    def get_pool_data_cgc(self,tokens):
        for token in tokens:
            pools = token['cgc_data']['relationships']['top_pools']['data']
            pool_address = ",".join([pool['id'][4:] for pool in pools])
            network = token['cmc_data']['platform']['name'].lower()
            url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/pools/multi/{pool_address}"
            response = requests.get(url, headers=self.cgc_headers).json()
            token['cgc_data']['pool_data'] = response['data']
        return tokens

    def get_top_pair(self):
        data = self.get_new_pairs_cmc()
        filtered_data = self.filter_security_tokens(data)
        return filtered_data
    
    def filter_burned_tokens(self,data):
        filtered_data = []
        for item in data:
            if item['address'] not in BURNED_ADDRESSES:
                filtered_data.append(item)
        return filtered_data

    def calculate_liquidity_metrics(self,tokens):
        for token in tokens:
            token["%_pooled"] = token['cmc_data']['pool_data']['percent_pooled_base_asset']
    
    def calculate_percentage_burned(self,tokens):
        for token in tokens:
            from_address = token['cmc_data']['pairContractAddress']
            to_address = BURNED_ADDRESSES 
            pass
    def liquidity_filter(self,data,filter_value = 100):
        filtered_data = []
        for item in data:
            if item['cmc_data']['quote'][0].get('liquidity') and item['cmc_data']['quote'][0]['liquidity'] <= filter_value:
                filtered_data.append(item)
        return filtered_data
    
    def total_supply_percentage_filter(self,data,filter_value = 0.99):
        filtered_data = []
        for item in data:
            if item['is_base_asset']:
                if (item['cmc_data'].get('percent_pooled_base_asset')) and (item['cmc_data']['percent_pooled_base_asset'] >= filter_value and item['cmc_data']['percent_pooled_base_asset'] <= 1):
                    filtered_data.append(item)
            else:
                filtered_data.append(item)
        return filtered_data
    
    def get_holders(self,data):
        for item in data:
            address = item['cmc_data']['contract_address']
            url = f"https://bscscan.com/token/tokenholderchart/{address}"
            headers = {"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"}
            response = requests.get(url,headers=headers)
            soup = BeautifulSoup(response.text)
            table = soup.find_all('table')
            holders = []
            if len(table) > 0:
                tr = table[0].find_all('tr')
                if len(tr) > 0:
                    for row in tr:
                        holder = []
                        td = row.find_all('td')
                        if len(td) > 0:
                            for cell in row.contents[:-1]:
                                holder.append(cell.text.replace('\n',"").strip())
                            holders.append(holder.copy())
            if len(holders) > 0:
                formated_holders = []
                for holder in holders:
                    record = {
                        "ranking":holder[0],
                        "address":holder[1],
                        "quantity":holder[2],
                        "percentage":holder[3].replace("%","")
                    }
                    formated_holders.append(record)
                item['holders'] = formated_holders
            time.sleep(0.5)
        return data

    def filter_holders(self,data, percentage = 99):
        filtered_data = []
        locked_holder_keyword = ['pinksale']
        burned_holder_keyword = ['0x000']
        
        for item in data:
            if len(item['holders']) > 0:
                locked_percentage = 0
                burned_percentage = 0
                for holder in item['holders']:
                    for k in locked_holder_keyword:
                        if k in holder['address'].lower():
                            locked_percentage += float(holder['percentage'])
                    for j in burned_holder_keyword:
                        if j in holder['address'].lower():
                            burned_percentage += float(holder['percentage'])
                if locked_percentage + burned_percentage > percentage:
                    filtered_data.append(item)            
        return filtered_data
    
    def add_validation_links(tokens,network="bsc"):
        if network == "bsc":
            goplus_network_id = '56'
        for token in tokens:
            token['validation_links'] = {
                "goplus":f"https://www.gopluslabs.io/token-security/{goplus_network_id}/{token['contract_address']}",
                "dexscreener":f"dexscreener.com/{network}/{token['contract_address']}",
                "bscscan":f"https://bscscan.com/token/tokenholderchart/{token['contract_address']}"

            }
        return tokens
    def rug_filter(self,tokens):
        filtered_tokens = []
        for token in tokens:
            if token['quote'][0].get('percent_change_price_1h')  > -0.97:
                filtered_tokens.append(token)
        return filtered_tokens
    
    def scan_quickintel(self,tokens,network="bsc"):
        for token in tokens:
            if token['is_base_asset']:
                token_address = token['cmc_data']['base_asset_contract_address']
            else:
                token_address = token['cmc_data']['quote_asset_contract_address']
            url = "https://app.quickintel.io/api/quicki/getquickiauditfull"
            body = {
                "chain": network,
                "tier": "basic",
                "tokenAddress": token_address
            }
            response = requests.post(url,json=body)
            token['quickintel_scan'] = response.json()
        return tokens
    
    def scan_goplus(self,tokens,network="bsc"):
        if network == "bsc":
            goplus_network_id = '56'
        
        for token in tokens:
            if token['is_base_asset']:
                token_address = token['cmc_data']['base_asset_contract_address']
            else:
                token_address = token['cmc_data']['quote_asset_contract_address']
            url = f"https://api.gopluslabs.io/api/v1/token_security/{goplus_network_id}?contract_addresses={token_address}"
            headers = {
                "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            }
            response = requests.get(url,headers=headers)
            if response.status_code == 200:
                token['goplus_scan'] = response.json()['result'][token_address]
                time.sleep(0.5)
        return tokens

    def scan_tokensniffer(self,tokens,network="bsc"):
        for token in tokens:
            url = f"https://tokensniffer.com/token/{network}/{token['cmc_data']['contract_address']}"
            headers = {
                "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            }
            response = requests.get(url,headers=headers)
            token['tokensnifferscan'] = response.json()
        return tokens
    
    def get_token_owner(self,token_address,network='bsc'):
        params = {
        "chain":network,
        "order": "DESC",
        "token_address": token_address
        }
        result = evm_api.token.get_token_owners(
        api_key=self.moralis_api_key,
        params=params,
        )

        print(result)
    
    def add_token_details(self,tokens):
        for token in tokens:
            if token['is_base_asset']:
                token_address = token['cmc_data']['base_asset_contract_address']
            else:
                token_address = token['cmc_data']['quote_asset_contract_address']
            url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/bsc/tokens/{token_address}"
            response = requests.get(url, headers=self.cgc_headers)
            token['token_details'] = response.json()
        return tokens
    
    def format_output(self,token):
        if token['is_base_asset']:
            token_address = token['cmc_data']['base_asset_contract_address']
            token_name = token['cmc_data']['base_asset_symbol']
        else:
            token_address = token['cmc_data']['quote_asset_contract_address']
            token_name = token['cmc_data']['quote_asset_symbol']
        pool_created_at = datetime.strptime(token['cgc_data']['attributes']['pool_created_at'], "%Y-%m-%dT%H:%M:%SZ")
        time_diff = datetime.now().utcnow() - pool_created_at
        pool_age_hour = time_diff.seconds//3600
        pool_age_min = (time_diff.seconds - pool_age_hour*3600)//60
        pool_age = f"{pool_age_hour}h {pool_age_min}m"
        
        if token['goplus_scan'].get('is_mintable') is None:
            mintable = True
        else:
            mintable = bool(int(token['goplus_scan'].get('is_mintable')))
        if token['cgc_data']['attributes']['market_cap_usd'] is None:
            market_cap  = "N/A"
        else:
            market_cap = token['cgc_data']['attributes']['market_cap_usd']
        if mintable:
            mintable = 'Yes'
        else:
            mintable = 'No'

        freezeable = token['quickintel_scan']['quickiAudit'].get('contract_Renounced')
        if freezeable is None:
            freezeable = bool(int(token['goplus_scan']['can_take_back_ownership']))
        if freezeable:
            freezeable = 'Yes'
        else:
            freezeable = 'No'
        holder_percentage = 0
        if token['goplus_scan'].get('holders'):
            for holder in token['goplus_scan']['holders']:
                holder_percentage += float(holder['percent'])
        elif token['goplus_scan'].get('lp_holders'):
            for holder in token['goplus_scan']['lp_holders']:
                holder_percentage += float(holder['percent'])
        content = f"""<b>🚀 Token Details:  {token['cmc_data']['base_asset_name']}</b> ${token_name}
- 💳 Contract: <code>{token_address}</code>
- USD: {token['cgc_data']['attributes']['base_token_price_usd']}
- Market cap: {market_cap}
- Vol 24h: {token['cgc_data']['attributes']['volume_usd']['h24']}
- Pool age: {pool_age}
  
<b>💡Security:</b>
- Top 10: {int(holder_percentage*100)}%
- LP: {int(token['cmc_data']['percent_pooled_base_asset']*100)}%
- Mintable: {mintable}
- Freezable: {freezeable}
<b>Links:</b>
<a href="https://dexscreener.com/bsc/{token['cmc_data']['contract_address']}">DexScreener</a>
<a href="https://gmgn.ai/bsc/token/{token_address}">Gmgn</a>
<a href="https://t.me/GMGN_sol_bot?start=i_BNKuCPoo">Gmgn Bot</a>
"""
        return content
    def post_to_telegram(self,content):
        asyncio.run(self.telegram_bot.send_message(chat_id='addas',msg = content, parse_mode="HTML"))
        self.telegram_bot.send_message(chat_id='addas',msg = content)
        print("Content posted to Telegram successfully.")
    

    def insert_to_mongo(self,content,token):
        mydb = self.mongo_client["sightsea"]
        mycol = mydb["liquidity_contents"]
        record = {
            "content":content,
            "created_at":datetime.now(),
            "updated_at":datetime.now(),
            "token_data":token
        }
        mycol.insert_one(record)
    
    def filter_security_project(self,tokens):
        filtered_data = []
        for token in tokens:
            if token['quickintel_scan']['contractVerified'] == False:
                continue
            if bool(int(token['goplus_scan']['is_open_source'])) == False:
                continue
            filtered_data.append(token)
        return filtered_data
        
        
    
if __name__ == "__main__":
    client = LiquidityBot()
    #cmc_pools = client.get_new_pairs_cmc_pro()
    cgc_latest_pools = client.get_new_pairs_cgc_pro(pool_created_hour_max="1h")
    new_tokens = client.get_pool_data_cmc(cgc_latest_pools)
    #result = client.filter_security_tokens(new_tokens)
    filter_liquidity = client.liquidity_filter(new_tokens,1000)
    filter_total_supply = client.total_supply_percentage_filter(filter_liquidity,0)
    scan_goplus = client.scan_goplus(filter_total_supply)
    scan_quickintel = client.scan_quickintel(filter_total_supply)
    #token_w_holders = client.get_holders(scan_quickintel)
    filter_security = client.filter_security_project(scan_quickintel)
    add_token_price = client.add_token_details(filter_security)

    for token in add_token_price:
        content = client.format_output(token)   
        client.insert_to_mongo(content,token)
        #client.post_to_telegram(content)
    # token_w_holders = client.get_holders(filter_total_supply)
    
    # filterd_holders = client.filter_holders(token_w_holders)
    #rug_filter = client.rug_filter(filterd_holders)
    # add_quickintel = client.scan_quickintel(filterd_holders)
    # token_sniffer_scan = client.scan_tokensniffer(add_quickintel)

    pass
    
    
    
    #0x9afdd172ae444a0c99a3148eae72ac02c846421e



