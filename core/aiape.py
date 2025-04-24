import requests
import os, dotenv,sys

dotenv.load_dotenv()
CWD = os.getcwd()
sys.path.append(CWD)    
from moralis import evm_api, sol_api
import requests
from core.token_info import TokenInfo
import datetime
from time import time 
from x import post_to_twitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from core.query_templates import prompt as prompt_template
import json

class AIAPE:
    def __init__(self):
        self.moralis_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjgxZTY1Yjk4LTc5OGMtNDZlOS04Yjg2LTYzNTc5ZTgzMzBiMSIsIm9yZ0lkIjoiNDIyMDcxIiwidXNlcklkIjoiNDM0MDgxIiwidHlwZUlkIjoiZTU2MGEwNmQtMWUzYS00OTY3LWFlNTMtMjc3YzBkMjgxMmM2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3MzQ4MzY1NzgsImV4cCI6NDg5MDU5NjU3OH0.HRZOSN3-iN5hcWbIot444zcoY5_BIfD5322cuZWDCUE'
        self.moralis_headers = {
            "Accept": "application/json",
            "X-API-Key": self.moralis_api_key
        }
        self.cgc_headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": os.getenv('COINGECKO_API_KEY')
        }
        self.cmc_headers = {
            "accept":"application/json",
            "X-CMC_PRO_API_KEY":os.getenv("CMC_DEXSCAN_API_KEY")
        }
        self.llm = ChatOpenAI(model='gpt-4o-mini')
    
    def get_cgc_categories(self):
        url = "https://pro-api.coingecko.com/api/v3/onchain/categories?sort=h24_tx_count_desc"
        response = requests.get(url, headers=self.cgc_headers)
        self.top_cgc_categories = response.json()['data']
        return self.top_cgc_categories
    
    def get_top_trending_pool(self, category, hours=1):

        url =  f"https://pro-api.coingecko.com/api/v3/onchain/categories/{category}/pools"
        if hours == 1:
            params = {
                "sort": "h1_trending",
                "per_page": 1,
                "page": 1
            }
        elif hours == 6:
            params = {
                "sort": "h6_trending",
                "per_page": 1,
                "page": 1
            }
        response = requests.get(url, headers=self.cgc_headers,params=params)
        self.trending_pool = response.json()['data']
        return self.trending_pool

    def get_ohlcv(self,pool_address,network,interval='1'):
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/pools/{pool_address}/ohlcv/hour"
        params = {
            "aggregate": interval,
            "before_timestamp": int(datetime.datetime.now().timestamp()),
            "limit": 24,

        }
        response = requests.get(url, headers=self.cgc_headers,params=params)
        self.ohlcv = response.json()['data']
        return self.ohlcv['attributes']['ohlcv_list']
    
    def get_pool_info(self,total,category):
        pool_data = self.trending_pool[:total]
        results = []
        narative = category['attributes']['name']
        for pool in pool_data:
            pool_address = pool['attributes']['address']
            network = pool['relationships']['network']['data']['id']
            base_token_address = pool['relationships']['base_token']['data']['id'].replace(f"{network}_","")
            if network in ['solana','eth', '0x1', 'sepolia', '0xaa36a7', 'polygon', '0x89', 'bsc', '0x38', 'bsc testnet', '0x61', 'avalanche', '0xa86a', 'fantom', '0xfa', 'palm', '0x2a15c308d', 'cronos', '0x19', 'arbitrum', '0xa4b1', 'chiliz', '0x15b38', 'chiliz testnet', '0x15b32', 'gnosis', '0x64', 'gnosis testnet', '0x27d8', 'base', '0x2105', 'base sepolia', '0x14a34', 'optimism', '0xa', 'holesky', '0x4268', 'polygon amoy', '0x13882', 'linea', '0xe708', 'moonbeam', '0x504', 'moonriver', '0x505', 'moonbase', '0x507', 'linea sepolia', '0xe705']:
                token_info = TokenInfo(token_address=base_token_address,network=network)
                token_info.get_moralis_data()
                token_info.get_cgc_data()
                pool_ohlcv = self.get_ohlcv(pool_address,network)
                results.append({
                    "narrative": narative,
                    "pool_address": pool_address,
                    "base_token_address": base_token_address,
                    "network": network,
                    "pool_data": pool,
                    "ohlcv": pool_ohlcv,
                    "token_info": token_info,
                })
        return results
            #content = self.generate_content(token_info,narative,pool_ohlcv)
            #post_to_twitter(content)

        
        



    def generate_content(self, token_info,narrative,ohlcv):
        # Generate content using the token_info object
        # This is a placeholder for the actual content generation logic
        token_symbol = token_info.cgc_data['attributes']['symbol']
        vol_up = int((ohlcv[1][-1] / ohlcv[-1][-1])*100)
        marketcap = token_info.cgc_data['attributes']['fdv_usd']

        content = f"""
        Trending on {narrative}, ${token_symbol} showing signs, vol up {vol_up}% past 24h, mc ${marketcap}, built on {token_info.network}, contract {token_info.token_address}, looks like something’s brewing right now.      
        """
        post_content = self.rephrase_content(content)
        return post_content
    def generate_ai_content(self, token_info,narrative,ohlcv):
        token_symbol = token_info.cgc_data['attributes']['symbol']
        volume_increase = int((ohlcv[1][-1] / ohlcv[-1][-1])*100)
        marketcap = token_info.cgc_data['attributes']['fdv_usd']
        prompt = PromptTemplate(
            template = prompt_template.REPHRASE_X_POST,
            input_variables=["context"],
            partial_variables={
                "token_symbol": token_symbol,
                "narrative": narrative,
                "volume_increase": volume_increase,
                "token_address": token_info.token_address,
                "network": token_info.network,
                "market_cap": marketcap
                }
            )
        chain = chain = prompt | self.llm
        res = chain.invoke({"context": None})
        if isinstance(res,dict):
            return res['output_text']
        else:
            return res.content
    
    def filter_tokens(self):
        categories = aiape.get_cgc_categories()
        for category in categories:
            aiape.get_top_trending_pool(category['id'],hours=6)
            pool_data = aiape.get_pool_info(15,category)
            for pool in pool_data:
                liquidity = pool['token_info'].moralis_data['token_analytics'].get('totalLiquidityUsd')
                fdv = pool['token_info'].moralis_data['token_analytics'].get('totalFullyDilutedValuation')
                buy_volume_24h = pool['token_info'].moralis_data['token_analytics'].get('totalBuyVolume').get('24h')
                buy_volume_1h = pool['token_info'].moralis_data['token_analytics'].get('totalBuyVolume').get('1h')
                date_format = "%Y-%m-%dT%H:%M:%SZ"
                pool_created_at = datetime.datetime.strptime(pool['pool_data']['attributes']['pool_created_at'], date_format)
                pair_age  = datetime.datetime.now().utcnow() - pool_created_at
                with open('last_posted.json', 'r') as f:
                    last_posted = json.load(f)
                    if pool['pool_data']['attributes']['address'] in last_posted['pool_addresses']:
                        continue
                if not(liquidity and float(liquidity) >= 150000):
                    continue
                if not(fdv and 500000 <= float(fdv) <= 3000000):
                    continue
                if not(buy_volume_24h and float(buy_volume_24h) >= 50000):
                    continue
                if not(buy_volume_1h and float(buy_volume_1h) >= 50000):
                    continue
                if not(pair_age and pair_age.days <=5 and pair_age.seconds >= 60*60):
                    continue
                if len(last_posted) > 4:
                    last_posted['pool_addresses'].pop(0)
                    last_posted['pool_addresses'].append(pool['pool_data']['attributes']['address'])
                else:
                    last_posted['pool_addresses'].append(pool['pool_data']['attributes']['address'])
                with open('last_posted.json', 'w') as f:
                    f.write(json.dumps(last_posted))
                return pool
    

if __name__ == "__main__":
    aiape = AIAPE()
    result = aiape.filter_tokens()
    content = aiape.generate_ai_content(result['token_info'],result['narrative'],result['ohlcv'])
    post_to_twitter(content,env="prod")
    # aiape.get_top_trending_pool('stablecoins')