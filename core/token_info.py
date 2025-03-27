import requests
import os, dotenv,sys

dotenv.load_dotenv()
CWD = os.getcwd()
sys.path.append(CWD)    
from moralis import evm_api, sol_api
import pandas as pd
import time
from core.x import post_to_twitter
import asyncio
from core.telegram_bot import TelegramBot
from datetime import datetime


class TokenInfo:
    def __init__(self,token_address,network=None):
        self.token_address = token_address
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
        if network:
            self.network = network
        else:
            self.cgc_token_data, self.network = self.detect_network()
        self.quickintel_data = None
        self.goplus_data = None
        self.moralis_data = {}
    
    def list_networks(self):
        url = "https://pro-api.coingecko.com/api/v3/onchain/networks"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    
    def token_search(self):
        url = "https://deep-index.moralis.io/api/v2.2/tokens/search?query={self.token_address}"
        response = requests.get(url, headers=self.moralis_headers)
        return response.json()


    
    def detect_network(self):
        networks = ['eth','bsc','polygon','solana','base','ftm','ronin']
        self.found = False
        for network in networks:
            url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{self.token_address}?include=top_pools"
            response = requests.get(url, headers=self.cgc_headers)
            if response.status_code == 200:
                self.found = True
                return response.json(),network
        return None, None
        if not self.found:
            networks = self.list_networks()
            for network in networks['data']:
                url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network['id']}/tokens/{self.token_address}/info"
                query_params ={
                    "include":"top_pools"
                }
                response = requests.get(url, headers=self.cgc_headers,params=query_params)
                if response.status_code == 200:
                    self.found = True
                    return response.json(),network
        return None, None
    
    def get_token_price_data_cgc(self,network,contract_address):
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{contract_address}"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    def get_token_price_data_cmc(self):
        params = {
            "contract_address":self.token_address,
            "network_slug":self.network
        }
        url = f"https://pro-api.coinmarketcap.com/v4/dex/pairs/ohlcv/historical"
        response = requests.get(url, headers=self.cmc_headers,params=params)
        self.cmc_data =  response.json()
    
    def get_top_holders(self):
        url = f"https://api.covalenthq.com/v1/{self.network}/tokens/{self.token_address}/token_holders/"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    
    def get_moralis_data(self):
        url = f"https://deep-index.moralis.io/api/v2.2/tokens/{self.token_address}/analytics?chain={self.network}"
        res = requests.get(url, headers=self.moralis_headers)
        self.moralis_data['token_analytics'] = res.json()
        if self.network == 'solana':
            params = {
            "network": "mainnet",
            "address": self.token_address
            }
            result = sol_api.token.get_token_price(
            api_key=self.moralis_api_key,
            params=params,
            )
            self.moralis_data['token_price'] = result
        else:
            params = {
                "chain": self.network,
                "include": "percent_change",
                "address": self.token_address
                }
            result = evm_api.token.get_token_price(api_key=self.moralis_api_key, params=params)
            self.moralis_data['token_price'] = result
    
    def get_profit_wallet_by_token(self):
        if self.network == "ethereum":
            network = "eth"
        elif self.network == "solana":
            network = "sol"
        else:
            network = self.network
        params = {
            "chain": network,
            "address": self.token_address
            }
        try:
            result = evm_api.token.get_top_profitable_wallet_per_token(
            api_key=self.moralis_api_key,
            params=params,
            )
        except:
            result = None
        return result
    
    def scan_quickintel(self):
        url = "https://app.quickintel.io/api/quicki/getquickiauditfull"
        body = {
            "chain": self.network,
            "tier": "basic",
            "tokenAddress":  self.token_address
        }
        response = requests.post(url,json=body)
        self.quickintel_data = response.json()
    
    def scan_goplus(self):
        if self.network == "bsc":
            goplus_network_id = '56'
        
            
        url = f"https://api.gopluslabs.io/api/v1/token_security/{goplus_network_id}?contract_addresses={self.token_address}"
        headers = {
            "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            self.goplus_data = response.json()['result'][self.token_address]
            time.sleep(0.5)
    def generate_content(self,token_info):
        
        if token_info.network == "solana":
            gmgn_network = "sol"
        else:
            gmgn_network = token_info.network
    #     old_content = f"""<b>🚀 Token Details:  {token['cmc_data']['base_asset_name']}</b> ${token_name}
    # - 💳 Contract: <code>{token_address}</code>
    # - USD: {token['cgc_data']['attributes']['base_token_price_usd']}
    # - Market cap: {market_cap}
    # - Vol 24h: {token['cgc_data']['attributes']['volume_usd']['h24']}
    # - Pool age: {pool_age}
    
    # <b>💡Security:</b>
    # - Top 10: {int(holder_percentage*100)}%
    # - LP: {int(token['cmc_data']['percent_pooled_base_asset']*100)}%
    # - Mintable: {mintable}
    # - Freezable: {freezeable}
    # <b>Links:</b>
    # <a href="https://dexscreener.com/bsc/{token['cmc_data']['contract_address']}">DexScreener</a>
    # <a href="https://gmgn.ai/bsc/token/{token_address}">Gmgn</a>
    # <a href="https://t.me/GMGN_sol_bot?start=i_BNKuCPoo">Gmgn Bot</a>
    # """
        price_in_usd = round(token_info.moralis_data['token_price']['usdPrice'],4)
        price_24hr_change = round(token_info.moralis_data['token_price']['usdPrice24hrPercentChange'],2)
        #fdv = float(token_info.cgc_token_data['data']['attributes']['fdv_usd'])
        fdv  = float(token_info.moralis_data['token_analytics']['totalFullyDilutedValuation'])
        if fdv > 1000000:
            market_cap = f"${round(fdv/1000000,2)}M"
        elif fdv > 1000:
            market_cap = f"${round(fdv/1000,2)}K"
        else:
            market_cap = f"${fdv}"
        total_buy_h24 = float(token_info.moralis_data['token_analytics']['totalBuyVolume']['24h'])
        total_sell_h24 = float(token_info.moralis_data['token_analytics']['totalSellVolume']['24h'])
        h24_volume = total_buy_h24 + total_sell_h24
        #h24_volume = float(token_info.cgc_token_data['data']['attributes']['volume_usd']['h24'])
        if h24_volume> 1000000:
            volume = f"${round(h24_volume/1000000,2)}M"
        elif h24_volume > 1000:
            volume = f"${round(h24_volume/1000,2)}K"
        else:
            volume = f"${h24_volume}"
        #top_pools = token_info.cgc_token_data.get('included')
        # if top_pools and len(top_pools) > 0:
        #     top_pool = top_pools[0]
        #     pool_created_at = datetime.strptime(top_pool['attributes']['pool_created_at'], "%Y-%m-%dT%H:%M:%SZ")
        #     time_diff = datetime.now().utcnow() - pool_created_at
        #     pool_age_hour = time_diff.seconds//3600
        #     pool_age_min = (time_diff.seconds - pool_age_hour*3600)//60
        #     pool_age = f"{pool_age_hour}h {pool_age_min}m"
        #     if top_pool['attributes']['price_change_percentage'].get('h1'):
        #         price_percentage_change_1h = top_pool['attributes']['price_change_percentage']['h1']
        #     else:
        #         price_percentage_change_1h = None
        price_percentage_change_1h = None
        token_address = token_info.moralis_data['token_price']['tokenAddress']
        content = f"""­
    🔸 {token_info.moralis_data['token_price']['name']} (${token_info.moralis_data['token_price']['symbol']})
    ├ <code>{token_info.moralis_data['token_price']['tokenAddress']}</code>
    └ #{token_info.network.upper()}

    📊 <b>Token Stats:</b>
    ├ USD:  {token_info.moralis_data['token_price']['usdPrice']} ({round(float(token_info.moralis_data['token_price']['usdPrice24hrPercentChange']),2)}%)
    ├ MC:   {market_cap}
    ├ Vol:  {volume}
    └ 1H:   {price_percentage_change_1h}%

    🔗 <b>Links:</b>
    ├ <a href="https://gmgn.ai/{gmgn_network}/token/{token_info.token_address}?ref=ty1GJmNe">Gmgn</a>
    └ <a href="https://dexscreener.com/{token_info.network}/{token_info.token_address}">DexScreener</a>

    💸 <a href="https://t.me/GMGN_sol_bot?start=i_BNKuCPoo">Trade on {token_info.network.upper()} with GMGN!</a>
    ***<i>Note: AIAPE MEME SIGNAL is currently in the Alpha phase. The signals are analyzed based on information collected from on-chain data, social platforms, and various other sources to identify potential meme tokens early. This should not be considered investment advice.</i>***
    """
        return content
def post_to_telegram(content,parse_mode='html'):
    telegram_bot = TelegramBot()
    asyncio.run(telegram_bot.send_message(chat_id='addas',msg = content,parse_mode=parse_mode))
    #telegram_bot.send_message(chat_id='addas',msg = content,parse_mode=parse_mode)
    print("Content posted to Telegram successfully.")
if __name__ == "__main__":
    token_address = "9WucnshVcJeZyTKHCdCUFN5pMShiCWSGLL9s8bMfSnaq"
    token_info = TokenInfo(token_address,network='solana')
    token_data = {}
    token_info.get_token_price_data_cmc()
    token_info.get_moralis_data()
    token_info.scan_quickintel()
    #token_info.scan_goplus()
    content = token_info.generate_content(token_info)
    post_to_telegram(content)

    # df = pd.read_csv("list_token_aMinh.csv")
    # addresses = df["address"].to_list()
    # result = []
    # for address in addresses:
    #     token_info = TokenInfo(address)
    #     if token_info.found:
    #         top_wallets = token_info.get_profit_wallet_by_token()
    #         if top_wallets is not None:
    #             for wallet in top_wallets['result']:
    #                 record = wallet.copy()
    #                 record['token_address'] = address
    #                 record['token_name'] = top_wallets['name']
    #                 record['token_symbol'] = top_wallets['symbol']
    #                 result.append(record)
    # df = pd.DataFrame(result)
    # df.to_csv("top_profit_wallets_aMinh.csv",index=False)
    