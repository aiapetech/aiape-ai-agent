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
import time


dotenv.load_dotenv()

NUMBER_OF_CATEGORY = 3
NUMBER_OF_PROJECT_TOKENS = 10
NUMBER_OF_FINAL_TOKENS = 10
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
        
    
    
    
    def get_token_obj(self,token: str):
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
    
    def get_token_market_data(self,token_obj):
        token_cgc_id = token_obj.cgc_id
        headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': self.settings.COINGECKO_API_KEY
        }
        params = {
            'ids': token_cgc_id,
            'vs_currency': 'usd'
        }
        market_url = f"{self.settings.COINGECKO_API_BASE_URL}/coins/markets"
        res = requests.get(url=market_url,params=params,headers=headers).json()
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

    def get_token_info(self,token_obj,params=None):
        if type(token_obj) == str:
            cgc_id = token_obj
        else:
            cgc_id = token_obj.cgc_id
        headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': self.settings.COINGECKO_API_KEY
        }
        if params is None:
            params = {
                "comnunity_data": True,
                "developer_data": False,
                "market_data": True
            }
        info_url = f"{self.settings.COINGECKO_API_BASE_URL}/coins/{cgc_id}"
        token_info =  requests.get(url=info_url,params=params,headers=headers).json()
        time.sleep(0.3)
        return token_info
    def get_list_of_token_in_category(self,category_id,params=None):
        url =f"{self.settings.COINGECKO_API_BASE_URL}/coins/markets"
        headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': self.settings.COINGECKO_API_KEY
        }
        if params is None:
            params = {
                "vs_currency": 'usd',
                "category": category_id,
                "order": 'market_cap_desc',
                'per_page': 100,
                'page': 1,
                'sparkline': False,
                'locale': 'en'

            }
        result =  requests.get(url=url,params=params,headers=headers).json()
        return result

    def get_category_list(self):
        headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': self.settings.COINGECKO_API_KEY
        }
        data = []
        url = f"{self.settings.COINGECKO_API_BASE_URL}/coins/categories"
        response = requests.get(url, headers=headers)
        return response.json()
        
    def get_category_data_by_token(self,token_data, category_list):
        token_categories= token_data['categories']
        category_data = []
        for category in category_list:
            if category['name'] in token_categories:
                category_data.append(category)     
        return category_data

    def calculate_score(self,token: dict,date =None):
        if date is None:
            date = datetime.now().date()
        else:
            date = datetime.strptime(date,'%Y-%m-%d')
        # with Session(postgres_engine) as session:
        #     token_market_data = session.exec(select(TokenMarketData).where(TokenMarketData.symbol == token['symbol']).where(TokenMarketData.name == token['name']).where(cast(TokenMarketData.last_updated, Date) == date)).first()
        market_cap_change = token['market_cap_change_percentage_24h']
        price_change_percentage_24h = token['price_change_percentage_24h']
        if market_cap_change is None:
            score = price_change_percentage_24h
        else:
            score = 0.4*market_cap_change + price_change_percentage_24h*0.6
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
        token_objs = []
        values = []
        for project_name in set(project_names):
            token_obj = self.get_token_obj(project_name)
            if token_obj is None:
                print(f"Token {project_name} not found")
                continue
            token_objs.append(self.get_token_info(token_obj))
            #token_objs.append(token_obj)
            #token_symbols.append(token_obj.symbol)
        #df_token_market_data = pd.read_sql(f"SELECT * FROM token_market_data where symbol in {tuple(token_symbols)} and date(last_updated) = '{processed_date}'", postgres_engine)
        # df_token_market_data = 
        # values = df_token_market_data.to_dict("records")
        df_project_tokens = pd.DataFrame(token_objs)
        df_project_tokens['score'] = df_project_tokens.apply(lambda x: self.calculate_score(x['market_data']),axis=1)
        # token_market_data = [v['market_data'] for v in token_objs]
        # df_token_market_data = pd.DataFrame(token_market_data)
        # df_token_market_data['score'] = df_token_market_data.apply(lambda x: self.calculate_score(x['market_data']),axis=1)
        # for token in token_objs: 
        #     score = self.calculate_score(token['market_data'])
        #     scrores.append(
        #             {
        #                 'token': token['symbol'],
        #                 'name': token['name'],
        #                 'score': score,
        #                 "date": processed_date
        #             }
        #         )
            
        df_project_tokens = df_project_tokens.sort_values(by='score',ascending=False)
        top_token_objs = df_project_tokens.head(NUMBER_OF_PROJECT_TOKENS).to_dict("records")
        category_list = self.extract_category(top_token_objs)
        df_category = pd.DataFrame(category_list).sort_values(by='market_cap',ascending=False)
        category_top_list = df_category.to_dict("records")
        top_token_each_category = []
        for category in category_top_list:
            top_token_each_category += category['top_3_coins_id']
        top_token_each_category = list(set(top_token_each_category))[:NUMBER_OF_FINAL_TOKENS]
        final_token_data = []
        for token in top_token_each_category:
            final_token_data.append(self.get_token_info(token))
        return df_project_tokens, df_category, final_token_data

    def calculate_market_cap_percentage_change(self,x):
        return x['market_cap_change_24h']/(x['market_cap']-x['market_cap_change_24h']) if x['market_cap'] else None

    def get_token_cgc_id(self,project,cgc_coin_list):
        project_name = project.split(',')[1].lower().strip()
        project_symbol = project.split(',')[0].strip().lower()
        cgc_id = next((item for item in cgc_coin_list if item["name"].lower() == project_name and item["symbol"].lower() == project_symbol), None)
        if cgc_id is None:
            return None
        return cgc_id['id']
    
    def generate_report_v2(self,df_extracted_project_name):
        cgc_ids = df_extracted_project_name.project_id.unique().tolist()
        token_objs = []
        for cgc_id in set(cgc_ids[:30]):
            token_objs.append(self.get_token_info(cgc_id))
            #token_objs.append(token_obj)
            #token_symbols.append(token_obj.symbol)
        #df_token_market_data = pd.read_sql(f"SELECT * FROM token_market_data where symbol in {tuple(token_symbols)} and date(last_updated) = '{processed_date}'", postgres_engine)
        # df_token_market_data = 
        # values = df_token_market_data.to_dict("records")
        df_project_tokens = pd.DataFrame(token_objs)
        df_project_tokens['score'] = df_project_tokens.apply(lambda x: self.calculate_score(x['market_data']),axis=1)
        # token_market_data = [v['market_data'] for v in token_objs]
        # df_token_market_data = pd.DataFrame(token_market_data)
        # df_token_market_data['score'] = df_token_market_data.apply(lambda x: self.calculate_score(x['market_data']),axis=1)
        # for token in token_objs: 
        #     score = self.calculate_score(token['market_data'])
        #     scrores.append(
        #             {
        #                 'token': token['symbol'],
        #                 'name': token['name'],
        #                 'score': score,
        #                 "date": processed_date
        #             }
        #         )
            
        df_project_tokens = df_project_tokens.sort_values(by='score',ascending=False)
        top_token_objs = df_project_tokens.head(NUMBER_OF_PROJECT_TOKENS).to_dict("records")
        category_list = self.extract_category(top_token_objs)
        df_category = pd.DataFrame(category_list).sort_values(by='market_cap',ascending=False)
        df_category['market_cap_percentage_change_24h'] = df_category.apply(lambda x: self.calculate_market_cap_percentage_change(x), axis=1)
        category_top_list = df_category.to_dict("records")
        top_potential_token = []
        for category in category_top_list[:NUMBER_OF_CATEGORY]:
            top_100_token = self.get_list_of_token_in_category(category['id'])
            top_potential_token += top_100_token
        df_top_potential_tokens = pd.DataFrame(top_potential_token)
        df_top_potential_tokens['score'] = df_top_potential_tokens.apply(lambda x: self.calculate_score(x),axis=1)
        df_top_potential_tokens.drop_duplicates(subset=['id'],inplace=True)
        df_top_potential_tokens = df_top_potential_tokens.sort_values(by='score',ascending=False)
        
        final_token_data = []
        # for token in top_token_each_category:
        #     final_token_data.append(self.get_token_info(token))
        return df_project_tokens, df_category, df_top_potential_tokens

    def extract_category(self,top_tokens):
        category_list = self.get_category_list()
        category_data = []
        for token_data in top_tokens:
            token_categories= token_data['categories']
            for category in category_list:
                if category['name'] in token_categories:
                    category_data.append(category)     
        category_name = []
        category_unique= []
        for category in category_data:
            if category['name'] in category_name:
                continue    
            category_unique.append(category)
            category_name.append(category['name'])
        return category_unique
    
        


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
    df = pd.read_csv('test_project.csv')
    token_info.generate_report_v2(df)
    # project_name = 'ETH, Ethereum'
    # token = token_info.get_token_info(project_name)
    # pass
    #df_scrores, df_token_market_data = token_info.generate_report('2025-01-26')
    
    #token_info.get_category_list()
    