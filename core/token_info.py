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
from datetime import datetime, timedelta, UTC
from sqlalchemy import create_engine
from models.postgres_models import TokenFollowings
from sqlalchemy import URL
from sqlalchemy.orm import sessionmaker



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
            url = f"https://solana-gateway.moralis.io/token/mainnet/{self.token_address}/metadata"
            response = requests.get(url, headers=self.moralis_headers)
            self.moralis_data['token_metadata'] = response.json()
        else:
            params = {
                "chain": self.network,
                "include": "percent_change",
                "address": self.token_address
                }
            result = evm_api.token.get_token_price(api_key=self.moralis_api_key, params=params)
            self.moralis_data['token_price'] = result
            params = {
            "chain": self.network,
            "addresses":[self.token_address]
            }

            result = evm_api.token.get_token_metadata(
            api_key=self.moralis_api_key,
            params=params,
            )
            if type(result) == list and len(result) > 0:
                result = result[0]
            self.moralis_data['token_metadata'] = result
        if self.moralis_data.get("token_price"):
            pair_address = self.moralis_data['token_price']['pairAddress']
            params = {
                "chain": self.network,
                "timeframe": '1h',
                "currency": 'usd',
                "fromDate": (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d"),
                "toDate":(datetime.now(UTC)+timedelta(days=1)).strftime("%Y-%m-%d"),
                "limit":24,

            }
            if self.network == "solana":
                url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pair_address}/ohlcv"
            else:
                url = f"https://deep-index.moralis.io/api/v2.2/pairs/{pair_address}/ohlcv"
            response = requests.get(url, headers=self.moralis_headers,params=params)
            self.moralis_data['ohlcv'] = response.json()

    
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
        #fdv = float(token_info.cgc_token_data['data']['attributes']['fdv_usd'])
        if token_info.moralis_data['token_metadata'].get('fullyDilutedValue'):
            fdv  = float(token_info.moralis_data['token_metadata']['fullyDilutedValue'])
        elif token_info.moralis_data['token_metadata'].get('fully_diluted_valuation'):
            fdv = float(token_info.moralis_data['token_metadata']['fully_diluted_valuation'])
        else:
            fdv = None
        if fdv:
            if fdv > 1000000:
                market_cap = f"${round(fdv/1000000,2)}M"
            elif fdv > 1000:
                market_cap = f"${round(fdv/1000,2)}K"
            else:
                market_cap = f"${fdv}"
        else:
            market_cap = "N/A"
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
        if token_info.moralis_data['token_metadata'].get('name'):
            token_name = token_info.moralis_data['token_metadata']['name']
        elif token_info.moralis_data['token_price'].get('name'):
            token_name = token_info.moralis_data['token_price']['name']
        else:
            token_name  = token_info.quickintel_data['tokenDetails']['tokenName']

        if  token_info.moralis_data['token_metadata'].get('symbol'):
            token_symbol = token_info.moralis_data['token_metadata']['symbol']
        elif token_info.moralis_data['token_price'].get('symbol'):
            token_symbol = token_info.moralis_data['token_price']['symbol']
        else:
            token_symbol = token_info.quickintel_data['tokenDetails']['tokenSymbol']
        price_percentage_change_1h = "N/A"
        try :
            if token_info.moralis_data.get('ohlcv'):
                result = token_info.moralis_data['ohlcv']['result']
                if len(result) > 1:
                    price_now = result[0]['close']
                    price_1h_ago = result[1]['close']
                    price_percentage_change_1h = round((price_now - price_1h_ago)/price_1h_ago*100,2)
            else:
                price_percentage_change_1h = "N/A"
        except Exception as e:
            price_percentage_change_1h = "N/A"

        content = f"""­
    🔸<a href="https://gmgn.ai/{gmgn_network}/token/{token_info.token_address}?ref=ty1GJmNe"><b>{token_name}</b></a> (<a href="https://t.me/AIxAPE"><b>${token_symbol}</b></a>)🔥
    ├ <code>{token_info.token_address}</code>
    └ #{token_info.network.upper()}

    📊 <b>Token Stats:</b>
    ├ USD:  {token_info.moralis_data['token_price']['usdPrice']} ({round(float(token_info.moralis_data['token_price']['usdPrice24hrPercentChange']),2) if token_info.moralis_data['token_price'].get('usdPrice24hrPercentChange') else None}%)
    ├ MC:   {market_cap}
    ├ Vol:  {volume}
    └ 1H:   {price_percentage_change_1h}%

    🔗 <b>Links:</b>
    ├ <a href="https://gmgn.ai/{gmgn_network}/token/{token_info.token_address}?ref=ty1GJmNe">Gmgn</a>
    └ <a href="https://dexscreener.com/{token_info.network}/{token_info.token_address}">DexScreener</a>

    💸 <a href="https://t.me/GMGN_sol_bot?start=i_BNKuCPoo"><b>Trade on {token_info.network.upper()} with GMGN!</b></a>
    
    
    ***<i>Note: AIAPE MEME SIGNAL is currently in the Alpha phase. The signals are analyzed based on information collected from on-chain data, social platforms, and various other sources to identify potential meme tokens early. This should not be considered investment advice.</i>***
    """
        return content
    def generate_following_content(self, following_token):
        x = int(following_token.price/self.moralis_data['token_price']['usdPrice'])
        old_market_cap = following_token.market_cap
        if old_market_cap > 1000000:
            old_market_cap = f"${round(old_market_cap/1000000,2)}M"
        elif old_market_cap > 1000:
            old_market_cap = f"${round(old_market_cap/1000,2)}K"
        else:
            old_market_cap = f"${old_market_cap}"

        if self.moralis_data['token_metadata'].get('fullyDilutedValue'):
            fdv  = float(self.moralis_data['token_metadata']['fullyDilutedValue'])
        elif self.moralis_data['token_metadata'].get('fully_diluted_valuation'):
            fdv = float(self.moralis_data['token_metadata']['fully_diluted_valuation'])
        else:
            fdv = None
        if fdv:
            if fdv > 1000000:
                new_market_cap = f"${round(fdv/1000000,2)}M"
            elif fdv > 1000:
                new_market_cap = f"${round(fdv/1000,2)}K"
            else:
                new_market_cap = f"${fdv}"
        if  self.moralis_data['token_metadata'].get('symbol'):
            token_symbol = self.moralis_data['token_metadata']['symbol']
        elif self.moralis_data['token_price'].get('symbol'):
            token_symbol = self.moralis_data['token_price']['symbol']
        else:
            token_symbol = self.quickintel_data['tokenDetails']['tokenSymbol']
        content = f"""
🔥🔥🔥
Achievement Unlocked: <b>{x}!</b>
AIAPE made a {x} call on ${token_symbol}.
(Market cap called:{old_market_cap}) -> ({new_market_cap})
"""
        return content
def post_to_telegram(content,parse_mode='html',reply_message_id=None):
    telegram_bot = TelegramBot()
    results = asyncio.run(telegram_bot.send_message(chat_id='addas',msg = content,parse_mode=parse_mode,is_tested=True,reply_message_id=reply_message_id))
    #telegram_bot.send_message(chat_id='addas',msg = content,parse_mode=parse_mode)
    print("Content posted to Telegram successfully.")
    return results

def insert_to_db(record):
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(engine)
    session = Session()
    with Session() as session:
        # Create a new record
        new_record = TokenFollowings(**record)
        res =session.add(new_record)
        res = session.commit()
    return res

def follow_token():
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(engine)
    with Session() as session:
        token_followings = session.query(TokenFollowings).filter(TokenFollowings.follow_status == "active").all()
        for token_following in token_followings:
            follow_duration = datetime.now(UTC) - token_following.follow_at.replace(tzinfo=UTC)
            if follow_duration > timedelta(hours=24):
                token_following.follow_status = "inactive"
                session.commit()
            else:
                token_info = TokenInfo(token_following.address,network=token_following.network)
                token_info.get_moralis_data()
                token_info.scan_quickintel()
                content = token_info.generate_following_content(token_following)
                results = post_to_telegram(content,reply_message_id=token_following.message_id)
                
    
if __name__ == "__main__":
    follow_token()
    token_address = "EiKZAWphC65hFKz9kygWgKGcRZUGgdMmH2zSPtbGpump"
    token_info = TokenInfo(token_address,network='solana')
    token_data = {}
    token_info.get_token_price_data_cmc()
    token_info.get_moralis_data()
    token_info.scan_quickintel()
    #token_info.scan_goplus()
    content = token_info.generate_content(token_info)
    
    results = post_to_telegram(content)
    if len(results) > 0:
        for result in results:
            market_cap = token_info.moralis_data['token_metadata'].get('fullyDilutedValue')
            if market_cap is None:
                market_cap = token_info.moralis_data['token_metadata'].get('fully_diluted_valuation')
            if market_cap:
                market_cap = float(market_cap)
            inserted_record = {
                "address": token_address,
                "network": token_info.network,
                "name": token_info.moralis_data['token_metadata']['name'],
                "symbol": token_info.moralis_data['token_metadata']['symbol'],
                "follow_at": datetime.now(UTC),
                "follow_status":"active",
                "message_id":result['message_id'],
                "chat_id": result['chat_id'],
                "price": token_info.moralis_data['token_price']['usdPrice'],
                "market_cap": market_cap
            }
            insert_to_db(inserted_record)

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
