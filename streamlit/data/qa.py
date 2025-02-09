from openai import OpenAI
import streamlit as st
import pandas as pd
from core.db import engine as postgres_engine
from core.post_processing import ChainSetting
from core.qa_chat import QARetriver 
from core.score_calculation import TokenInfo, ScoreSetting
import time



st.title("Token Q&A")

def token_list():
    tokens = pd.read_sql("SELECT cgc_id from tokens", postgres_engine)
    return tokens

def token_selectbox(token_lists):
    option = st.selectbox(
                "Select token to ask our assistant",
                options = token_lists,
                index=None,
                placeholder=  "Select token to ask our assistant",
                on_change=None,
            )
    st.session_state.token_id = option
    if option:
        settings = ScoreSetting()
        token_info = TokenInfo(settings,postgres_engine)
        tokendata = token_info.get_token_info(option)
        url = tokendata['links']['homepage'][0]
        market_data = tokendata['market_data']
        settings = ChainSetting()
        qar = QARetriver(url,tokendata,settings )
        st.session_state.qar = qar

def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

token = token_list()
token_selectbox(token)

if "qar" not in st.session_state:
   st.session_state.qar = None

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        text = st.session_state.qar.retrieve(prompt)
        response = st.write_stream(response_generator(text))
    st.session_state.messages.append({"role": "assistant", "content": response})
