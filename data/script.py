import json
import os,sys
sys.path.append(os.getcwd())
from core.db import engine as postgres_engine
from models.postgres_models import Tokens, PostPersonas, TwitterCredentials
from sqlmodel import Field, Session
import glob
import pymongo
from core.config import settings
from apify_client import ApifyClient
import pandas as pd
from datetime import datetime


CWD = os.getcwd()


txtfiles = []
for file in glob.glob("*.txt"):
    txtfiles.append(file)

def remove_id_field(file_path,new_file_name):
    with open(file_path, 'r') as file:
        data = json.load(file)
    new_data = []
    
    for item in data:
        del item['id']
        new_data.append(f"{item["symbol"]}, {item['name']}")
    
    with open(new_file_name, 'w') as file:
        json.dump(new_data, file, indent=4)
def remove_id_field(file_path,new_file_name):
    file_path = '/Users/jean/Work/SightSea-AI/demo/backend/app/list_of_project_cgc_full.json'
    new_file_name = 'list_of_project_cgc.json'
    remove_id_field(file_path,new_file_name)

def import_tokens():
    with open('cgc_data.json') as f:
        data = json.load(f)
    with Session(postgres_engine) as session:
        for item in data:
            token = Tokens(
                cgc_id=item['id'],
                symbol=item['symbol'], 
                name=item['name'],
                market_cap_rank=item['market_cap_rank'],
                search_text=f"{item['symbol'].lower()} {item['name'].lower()}")
            session.add(token)
        session.commit()
# Example usage

def insert_post_mongo():
    my_json_list = [f for f in glob.glob("/Users/jean/Work/SightSea-AI/demo/backend/data/x_posts/dataset_twitter-scraper-lite_*.json")]
    data = []
    for file in my_json_list:
        with open(file) as f:
            json_data = json.load(f)
        data += json_data
    unique_data = []
    ids = []
    for data_item in data:
        id = data_item['id']
        if id not in ids:
            unique_data.append(data_item)
            ids.append(id)
    ## Initialize the mongo client
    client = pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
    a = client.list_database_names()
    mydb = client["sightsea"]
    mycol = mydb["posts"]
    x = mycol.delete_many({})

    x = mycol.insert_many(unique_data)
    print(x)


def update_mongo_posts(data):
    ids = [item['id'] for item in data]
    client = pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
    mydb = client["sightsea"]
    mycol = mydb["posts"]
    x = mycol.delete_many({"id": {"$in": ids}})
    x = mycol.insert_many(data)
    return x

def fix_date_format():
    client =  pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
    mydb = client["sightsea"]
    data =mydb.posts.find()
    formated_data = []
    for item in data:
        date_format = "%a %b %d %H:%M:%S %z %Y"
        item['createdAt'] = datetime.strptime(item['createdAt'], date_format)
        formated_data.append(item)
    x = mydb.posts.delete_many({})
    x = mydb.posts.insert_many(formated_data)
    return x
def get_apify_data():
    from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
    client = ApifyClient("apify_api_EeNIHl229p0nKY9zIjLWAKP5LS3Anw1MEUF5")
    with open(f"{CWD}/data/list_of_kols.json") as f:
            request = json.load(f)
    request['start'] = "2025-02-11"
    request['end'] = "2025-02-11"
    # Prepare the Actor input
    run_input = {
        "searchTerms": ["apify"],
        "sort": "Latest",
        "maxItems": 100
    }

    # Run the Actor and wait for it to finish
    run = client.actor("nfp1fpt5gUlBwPcor").call(run_input=run_input)
    items = []
    # Fetch and print Actor results from the run's dataset (if there are any)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        items.append(item)
        pass
    with open(f"{CWD}/data/apify_data.json", "w") as f:
        json.dump(items, f, indent=4)
    return items
    ## Create a database    
def delete_old_data():
    my_json_list = [f for f in glob.glob("/Users/jean/Work/SightSea-AI/demo/backend/data/x_posts/dataset_twitter-scraper-lite_*.json")]
    data = []
    for file in my_json_list:
        with open(file) as f:
            json_data = json.load(f)
        data += json_data
    delted_ids = [i['id'] for i in data]
    client = pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
    mydb = client["sightsea"]
    mycol = mydb["posts"]
    x = mycol.delete_many({"id": {"$in": delted_ids}})

def insert_post_personas_postgres():
    df = pd.read_csv('Crypto_Twitter_Personas.csv')
    records = df.to_dict(orient='records')
    with Session(postgres_engine) as session:
        for item in records:
            persona = PostPersonas(
                username = item['Username'],
                age = item['Age'],
                country = item['Country'],
                profession = item['Profession'],
                financial_status = item['Financial Status'],
                personality = item['Personality'],
                likes = item['Likes'],
                dislikes = item['Dislikes'],
                posting_style = item['Posting Style'],
                daily_post_frequency = item['Daily Post Frequency']
            )
            session.add(persona)
        session.commit()
    pass

def insert_x_secret_postgres():
    df = pd.read_csv('twitter_secret.csv')
    records = df.to_dict(orient='records')
    with Session(postgres_engine) as session:
        for item in records:
            persona = TwitterCredentials(
                app_id = item['app_id'],
                consumer_key = item['consumer_key'],
                consumer_secret = item['consumer_secret'],
                bearer_token = item['bearer_token'],
                access_token = item['access_token'],
                access_secret = item['access_token_secret'], 
            )
            session.add(persona)
        session.commit()
    pass
 
def process_data():
    df = pd.read_csv('top_profit_wallets_aMinh.csv')
    df = pd.read_csv('top_profit_wallets_aMinh.csv')
    df_procressed = df.groupby('address')["token_address"].count().reset_index()
    df_procressed.columns = ['wallet_address','count']
    df_procressed = df_procressed.sort_values('count',ascending=False)
    df_procressed.to_excel('top_profit_wallets_detail_2.xlsx',index=False)

if __name__ == '__main__':
    #insert_x_secret_postgres()
    process_data()
    # items =  get_apify_data()
    # update_mongo_posts(items)