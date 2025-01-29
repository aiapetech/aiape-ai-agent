import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import engine as postgres_engine
from models.postgres_models import *
import dotenv
from datetime import datetime
from sqlmodel import  Session,select
import json
import requests
from sqlalchemy import or_, and_
import pandas as pd
from sqlalchemy import cast, Date
from core.config import settings as app_settings

from sqlalchemy import asc


dotenv.load_dotenv()

class ScoreSetting:
    COINGECKO_API_BASE_URL = app_settings.COINGECKO_API_BASE_URL
    COIN_MARKET_CAP_API_BASE_URL = app_settings.COIN_MARKET_CAP_API_BASE_URL
    COINGECKO_API_KEY = app_settings.COINGECKO_API_KEY

class TokenInfo:
    TOPLIST = {
            "eth": "eth, ethereum",
            "btc": "btc, bitcoin",
        }
    def __init__(self, settings: ScoreSetting, postgres_engine):
        self.settings = settings
        self.postgres_engine = postgres_engine
        self.coingecko_api_base_url = None
        self.coin_market_cap_api_base_url = None
        
    
    
    
    def get_token_info(self,token: str):
        token = token.lower().strip().replace('$','')
        if token.split(',')[0].strip().lower() in self.TOPLIST.keys():
            token = self.TOPLIST[token.split(',')[0].strip().lower()]

        if len(token.split(',')) == 1:
            token_symbol = token.split(',')[0].strip().lower()
            token_name = token.split(',')[0].strip().lower()
            search_text = f"%{token_symbol}%"
        else:
            token_symbol = token.split(',')[0].strip().lower().replace('$','')
            token_name = token.split(',')[1].strip().lower().replace('$','')
            search_text = f"%{token_symbol} {token_name}%".replace("(","").replace(")","").replace("  "," ").strip()
        with Session(postgres_engine) as session:
            statement = select(Tokens).where(and_(Tokens.symbol == token_symbol, Tokens.search_text.like(search_text))).order_by(asc(Tokens.market_cap_rank))
            token_obj = session.exec(statement).first()
            if token_obj is None:
                statement = select(Tokens).where(and_(Tokens.symbol == token_symbol, Tokens.name.like(f'%{token_name}%'))).order_by(asc(Tokens.market_cap_rank))
                token_obj = session.exec(statement).first()
                if token_obj is None:
                    statement = select(Tokens).where(or_(Tokens.symbol == token_symbol, Tokens.name.like(f'%{token_name}%'),Tokens.cgc_id.like((f'%{token_name}%')))).order_by(asc(Tokens.market_cap_rank))
                    token_obj = session.exec(statement).first()
        return token_obj
    def get_token_data(self,token_obj):
        token_cgc_id = token_obj.cgc_id
        headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': self.settings.COINGECKO_API_KEY
        }
        params = {
            'ids': token_cgc_id,
            'vs_currency': 'usd'
        }
        url = f"{self.settings.COINGECKO_API_BASE_URL}/coins/markets"
        res = requests.get(url=url,params=params,headers=headers).json()
        if len(res) == 0:
            return None
        token_market_data = res[0]
        token_market_data['token_id'] = token_obj.id
        token_market_data.pop('id')
        with Session(postgres_engine) as session:
            current_token_statement = select(TokenMarketData).where(TokenMarketData.token_id == token_obj.id).where(cast(TokenMarketData.last_updated, Date) == datetime.now().date())
            current_token = session.exec(current_token_statement).first()
            if current_token:
                for key, value in token_market_data.items():
                    setattr(current_token,key,value)
                session.add(current_token)
            else:
                token_market_data_obj = TokenMarketData(**token_market_data)
                session.add(token_market_data_obj)
            session.commit()
        return token_market_data
    
    def calculate_score(self,token: dict,date =None):
        if date is None:
            date = datetime.now().date()
        else:
            date = datetime.strptime(date,'%Y-%m-%d')
        # with Session(postgres_engine) as session:
        #     token_market_data = session.exec(select(TokenMarketData).where(TokenMarketData.symbol == token['symbol']).where(TokenMarketData.name == token['name']).where(cast(TokenMarketData.last_updated, Date) == date)).first()
        price_change_24h = token['price_change_24h']
        price_change_percentage_24h = token['price_change_percentage_24h']
        score = price_change_24h * 0.4 + price_change_percentage_24h * 0.6
        return score
    
    def generate_report(self,processed_date):
        processed_results = pd.read_sql(f"SELECT pr.*, p.posted_at  FROM processed_results pr left join posts p on pr.post_id = p.id where date(p.posted_at) = '{processed_date}'", postgres_engine)
        projects = processed_results.project_name.unique().tolist()
        project_names = []
        scrores = []
        token_symbols = []
        for p in projects:
            ps = p.split(';')
            project_names += ps
        for project_name in set(project_names):
            token_obj = self.get_token_info(project_name)
            if token_obj is None:
                print(f"Token {project_name} not found")
                continue
            self.get_token_data(token_obj)
            token_symbols.append(token_obj.symbol)
        df_token_market_data = pd.read_sql(f"SELECT * FROM token_market_data where symbol in {tuple(token_symbols)}", postgres_engine)
        values = df_token_market_data.to_dict("records")
        for token in values: 
            score = self.calculate_score(token)
            scrores.append(
                    {
                        'token': token['symbol'],
                        'name': token['name'],
                        'score': score,
                        "date": processed_date
                    }
                )
        df_scrores = pd.DataFrame(scrores).sort_values(by='score',ascending=False)
        df_token_market_data = pd.read_sql(f"SELECT * FROM token_market_data where date(last_updated) = '{processed_date}'", postgres_engine)
        return df_scrores, df_token_market_data
    
    # def run_score_calculation(self,posted_date,token=None):
    #     if not token:
    #         tokens = pd.read_sql("SELECT * FROM processed_results w", postgres_engine)
    #     token_obj = self.get_token_info(token)
    #     token_market_data = self.get_token_data(token_obj)
    #     return df_scrores, df_token_market_data

if __name__ == '__main__':
    # settings = ScoreSetting()
    # token_info = TokenInfo(settings,postgres_engine)
    # tokens = ['ETH, Ethereum','BANANA, Banana Gun']
    # for token in tokens:
    #     token_market_data = token_info.get_token_data(token)
    #     score = token_info.calculate_score(token)
    settings = ScoreSetting()
    token_info = TokenInfo(settings,postgres_engine)
    # project_name = 'ETH, Ethereum'
    # token = token_info.get_token_info(project_name)
    # pass
    df_scrores, df_token_market_data = token_info.generate_report('2025-01-26')