import sys, os
from pathlib import Path
CWD = Path(__file__).parents[2]
sys.path.append(str(CWD))
from openai import OpenAI
import streamlit as st
import pandas as pd
from core.db import engine as postgres_engine
from core.post_processing import ChainSetting
from core.qa_chat import QARetriver 
from core.digital_ocean import DigitalOceanClient
from core.telegram_bot import TelegramBot
from core.token_info import TokenInfo
import time
import streamlit as st
import asyncio
from core.post_processing import ChainSetting, PostProcessor
from datetime import datetime, timedelta, UTC
from core.token_info import insert_to_db


st.title("Post to X and Telegram")

def upload_images(uploaded_file):
    digital_ocean_client = DigitalOceanClient()
    image_file = f"tmp/images/{uploaded_file.name}"
    with open(image_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
    url = digital_ocean_client.upload_file(image_file)
    st.session_state.image_url = url
    return image_file, url    

def persona_list():
    persona = pd.read_sql("SELECT * from post_personas where twitter_app_id is not null", postgres_engine)
    return persona.username.values.tolist()

def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def generate_conent(contract_address,network=None):
    token_info = TokenInfo(token_address=contract_address,network=network)
    token_data = {}
    token_info.get_token_price_data_cmc()
    token_info.get_moralis_data()
    token_info.scan_quickintel()
    #token_info.scan_goplus()
    st.session_state.post_content = token_info.generate_content(token_info)
    st.session_state.generated_content = True
    st.session_state.token_info = token_info



def post_to_telegram(is_tested=True):
    telegram_bot = TelegramBot()
    results = asyncio.run(telegram_bot.send_message(chat_id='addas',msg = st.session_state.post_content,parse_mode='html',is_tested=is_tested))
    st.success("Content posted to Telegram successfully.")
    st.session_state.posted = True
    for result in results:
        market_cap = st.session_state.token_info.moralis_data['token_metadata'].get('fullyDilutedValue')
        if market_cap is None:
            market_cap = st.session_state.token_info.moralis_data['token_metadata'].get('fully_diluted_valuation')
        if market_cap:
            market_cap = float(market_cap)
        inserted_record = {
                    "address": st.session_state.contract_address,
                    "network": st.session_state.token_info.network,
                    "name": st.session_state.token_info.moralis_data['token_metadata']['name'],
                    "symbol": st.session_state.token_info.moralis_data['token_metadata']['symbol'],
                    "follow_at": datetime.now(UTC),
                    "follow_status":"active",
                    "message_id":result['message_id'],
                    "chat_id": result['chat_id'],
                    "price": st.session_state.token_info.moralis_data['token_price']['usdPrice'],
                    "market_cap": market_cap
                }
        insert_to_db(inserted_record)
        st.success("Successfully follow token in 24 hours")


list_session_state = [
    'contract_address',
    'post_content',
    'generated_content',
    'token_info'
   
]
for state in list_session_state:
    if state not in st.session_state:
        st.session_state[state] = None
col1, col2 = st.columns([4,1])
with col1:
    contract_address = st.text_input("Please input contract address",key="contract_address")
with col2:
    network = st.selectbox("Network",['eth','bsc','polygon','solana','base','ftm','ronin'],key="network")
if contract_address:
    st.button('Generate Content', on_click=generate_conent,kwargs={"contract_address":st.session_state.contract_address,"network":st.session_state.network})
    if st.session_state.generated_content:
        st.markdown(st.session_state.post_content)
        col1,col2 = st.columns([1,1])
        with col1:
            st.button("Test post to Telegram", on_click=post_to_telegram,kwargs={"is_tested":True})
        with col2:
            st.button("Post to Telegram", on_click=post_to_telegram,kwargs={"is_tested":False})
else:
    st.warning("Please input contract address")

    
    

