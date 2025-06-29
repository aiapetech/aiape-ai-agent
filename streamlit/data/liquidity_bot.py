import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path
CWD = Path(__file__).parents[2]
sys.path.append(str(CWD))
from core.db import engine as postgres_engine
from datetime import datetime
from core.liquidity_bot import LiquidityBot
from core.telegram_bot import TelegramBot
#0x2ddC7513240A7B5b9CfFceC7c9092d345e55Bb2f

liquidity_bot_client = LiquidityBot()
def format_df(tokens):
    display_data = []
    for token in tokens:
        display_token = token.copy()
        display_token["liquidity"] = display_token["quote"][0].get("liquidity")
        display_token["volume_24h"] = display_token["quote"][0].get("volume_24h")
        display_token["price"] = display_token["quote"][0].get("price")
        display_token.pop("quote")
        if display_token.get("holders") and type(token.get("holders")) == list:
            holders_string = ""
            for holder in token.get("holders") :
                holders_string += f"{holder['address']}: {holder['percentage']} \n"
            display_token["holders"] = holders_string
        display_data.append(display_token)
    return pd.DataFrame(display_data)   
def format_df_w_lp(tokens):
    display_data = []
    for token in tokens:
        data = token["cmc_data"]["baseToken"]
        data["liquidity"] = token["cmc_data"].get("liquidity")
        data["marketCap"] = token["cmc_data"].get("marketCap")
        data["price"] = token["cmc_data"].get("priceUsd")
        percent_pooled_base_asset =0
        for pool_data in token["cmc_data"]["pool_data"]:
            percent_pooled_base_asset += pool_data["percent_pooled_base_asset"]
        data["percent_pooled_base_asset"] = percent_pooled_base_asset
        display_data.append(data)
    return pd.DataFrame(display_data)
def get_new_pair():
    cgc_latest_pools = liquidity_bot_client.get_new_pairs_cgc_pro(pool_created_hour_max=st.session_state.pool_created_hour_max)
    new_address = [pool['attributes']['address'] for pool in cgc_latest_pools]
    new_tokens = liquidity_bot_client.get_pool_data_cmc(new_address)
    st.session_state["tokens"] = new_tokens
    st.session_state.latest_data = True

states = [
    "All",
    "tokens",
    "latest_data",
    "security",
    "security_filter",
    "liquidity",
    "liquidity_filter",
    "holder",
    "holder_filter",
    "filter_holder",
    "filterd_holders",
    "holder_data",
    "rug",
    "rug_filter"
]
for state in states:
    if state not in st.session_state:
        st.session_state[state] = None

def filter_token_with_security():
    st.session_state.security = liquidity_bot_client.filter_security_tokens(st.session_state.tokens)
    st.session_state.security_filter = True

def filter_token_liquidity():
    filter_liquidity = liquidity_bot_client.liquidity_filter(st.session_state.security ,int(st.session_state.max_liquidity))

    st.session_state.liquidity = liquidity_bot_client.total_supply_percentage_filter(filter_liquidity,int(st.session_state.pool_asset_percentage)/100)
    st.session_state.liquidity_filter = True

def filter_holder():
    st.session_state.holder_data = liquidity_bot_client.get_holders(st.session_state.liquidity)
    st.session_state.filterd_holders = liquidity_bot_client.filter_holders(st.session_state.holder_data,st.session_state.min_locked_burned)
    st.session_state.filter_holder = True


def filter_rug():
    st.session_state.rug = liquidity_bot_client.rug_filter(st.session_state.filterd_holders)
    st.session_state.rug_filter = True


col1, col2 = st.columns([1,1])
with col2:
    st.button("Get latest on-chain data",on_click=get_new_pair)
with col1:
    st.number_input("Choose duration in hour",value=1,key="pool_created_hour_max")
if st.session_state.latest_data:
    placeholder_post = st.empty()
    st.caption("New pairs from Coinmarketcap")
    df = pd.DataFrame(format_df(st.session_state["tokens"]))
    st.dataframe(df)
    st.button("Filtered token with security",on_click=filter_token_with_security)
    if st.session_state.security_filter:
        st.caption("Filter security")
        df = pd.DataFrame(format_df(st.session_state.security))
        st.dataframe(df)
        col1, col2, col3 = st.columns([1,1,1])
        with col3:
            st.button("Filtered token with liquidity",on_click=filter_token_liquidity)
        with col1:
            st.number_input("Max liquidity",value=100,key="max_liquidity")
        with col2:
            st.number_input("Pool asset percentage %",value=100,key="pool_asset_percentage")
        if st.session_state.liquidity_filter:
            st.caption("Filter liquidity")
            df = pd.DataFrame(format_df(st.session_state.liquidity))
            st.dataframe(df)
            col1, col2 = st.columns([1,1])
            with col2:
                st.button("Get holders data",on_click=filter_holder)
            with col1:
                st.number_input("Mininum total locked and burned %",key="min_locked_burned")
            if st.session_state.filter_holder:
                st.caption("New pairs with holder data")
                df = pd.DataFrame(format_df(st.session_state.holder_data))
                st.dataframe(df)
                st.caption("Filter holders")
                df = pd.DataFrame(format_df(st.session_state.filterd_holders))
                st.dataframe(df)
                st.button("Filtered rug pull",on_click=filter_rug)
                if st.session_state.rug_filter:
                    st.caption("Rug pull tokens")
                    df = pd.DataFrame(format_df(st.session_state.rug))
                    st.dataframe(df)
