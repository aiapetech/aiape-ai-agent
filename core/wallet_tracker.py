import requests
import json
import moralis
import solana
from solana.rpc.api import Client
# from solders.pubkey import Pubkey
from solana.rpc.api import Pubkey
import os, dotenv
from telegram_bot import TelegramBot
import asyncio
from moralis import sol_api

dotenv.load_dotenv()
CWD = os.getcwd()

class WalletTracker:
    def __init__(self, wallet_address_info):
        self.wallet_address_info = wallet_address_info
        self.moralis_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjgxZTY1Yjk4LTc5OGMtNDZlOS04Yjg2LTYzNTc5ZTgzMzBiMSIsIm9yZ0lkIjoiNDIyMDcxIiwidXNlcklkIjoiNDM0MDgxIiwidHlwZUlkIjoiZTU2MGEwNmQtMWUzYS00OTY3LWFlNTMtMjc3YzBkMjgxMmM2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3MzQ4MzY1NzgsImV4cCI6NDg5MDU5NjU3OH0.HRZOSN3-iN5hcWbIot444zcoY5_BIfD5322cuZWDCUE'
        self.moralis_headers = {
            "Accept": "application/json",
            "X-API-Key": self.moralis_api_key
        }
        self.cgc_api_key = 'f1b1b9b0-7bca-4b3b-8b3b-4b3b3b3b3b3b'
        self.cgc_headers = {
            "accept": "application/json",
            "x-cg-pro-api-key": os.getenv('COINGECKO_API_KEY')
        }
        self.telegram_bot = TelegramBot()
        

    def get_sol_wallet_transactions(self):
        wallet_address = self.wallet_address_info['address']
        url = f"https://solana-gateway.moralis.io/account/mainnet/{wallet_address}/swaps?order=DESC"
        response = requests.get(url, headers=self.moralis_headers)
        transactions = response.json()
        return transactions['result']
    
    def get_latest_sol_wallet_transaction(self):
        transactions = self.get_sol_wallet_transactions()
        return transactions[0]
    
    def get_market_cap(self,network,contract_address):
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{contract_address}"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    
    def get_token_data(self,network,contract_address):
        url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/tokens/{contract_address}"
        response = requests.get(url, headers=self.cgc_headers)
        return response.json()
    
    def get_native_wallet_balance(self):
        params = {
            "network": "mainnet",
            "address": self.wallet_address_info['address']
        }
        result = sol_api.account.balance(
            api_key=self.moralis_api_key,
            params=params,
            )
        return result['solana']

    
    def format_response_text(self,transaction):
        if transaction['transactionType'] == 'buy':
            contract_address = transaction['bought']['address']
            network = 'solana'
        else:  
            contract_address = transaction['sold']['address']
            network = 'solana'
        wallet_balance = self.get_native_wallet_balance()
        token_data = self.get_token_data(network,contract_address)
        market_cap = float(token_data['data']['attributes']['total_supply'])*float(token_data['data']['attributes']['price_usd'])
        content = f"""
        {self.wallet_address_info["name"]}, a KOL with {int(self.wallet_address_info['followers_count']/1000)}K followers, just {transaction["transactionType"]} ${int(transaction['totalValueUsd'])} in ${transaction['pairLabel']} at ${int(market_cap/1000)}K MC!
CA: {contract_address}
Wallet: {self.wallet_address_info["address"]}
Wallet Balance: {wallet_balance} sol
    """
        return content
    
    
    def post_to_telegram(self,content):
        asyncio.run(self.telegram_bot.send_message(chat_id='addas',msg = content))
        self.telegram_bot.send_message(chat_id='addas',msg = content)
        print("Content posted to Telegram successfully.")

def list_all_wallets():
    with open("./data/top_gmgn_wallet.json") as f:
        wallets = json.load(f)
    return wallets['data']['rank']  

if __name__ == "__main__":
    wallets = list_all_wallets()
    for wallet in wallets[5:]:
        wallet_tracker = WalletTracker(wallet)
        transaction = wallet_tracker.get_latest_sol_wallet_transaction()
        content = wallet_tracker.format_response_text(transaction)
        #wallet_tracker.post_to_telegram(content)