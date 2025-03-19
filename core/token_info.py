import requests
import os, dotenv

dotenv.load_dotenv()
CWD = os.getcwd()
from moralis import evm_api
import pandas as pd

class TokenInfo:
    def __init__(self,token_address):
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
        self.cgc_token_data, self.network = self.detect_network()
    
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
    
    def get_token_price_data(self,network,contract_address):
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{contract_address}"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    
    def get_top_holders(self):
        url = f"https://api.covalenthq.com/v1/{network}/tokens/{contract_address}/token_holders/"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    
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
    
if __name__ == "__main__":
    df = pd.read_csv("list_token_aMinh.csv")
    addresses = df["address"].to_list()
    result = []
    for address in addresses:
        token_info = TokenInfo(address)
        if token_info.found:
            top_wallets = token_info.get_profit_wallet_by_token()
            if top_wallets is not None:
                for wallet in top_wallets['result']:
                    record = wallet.copy()
                    record['token_address'] = address
                    record['token_name'] = top_wallets['name']
                    record['token_symbol'] = top_wallets['symbol']
                    result.append(record)
    df = pd.DataFrame(result)
    df.to_csv("top_profit_wallets_aMinh.csv",index=False)
    