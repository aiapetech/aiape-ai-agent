import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path
CWD = Path(__file__).parents[2]
sys.path.append(str(CWD))
from core.db import engine as postgres_engine
from datetime import datetime
from core.post_processing import ChainSetting, PostProcessor
from core.score_calculation import ScoreSetting, TokenInfo
from models.postgres_models import ProcessedResults, TokenMarketData
from sqlmodel import Session, select



def get_postgres_data():
    posts = pd.read_sql("SELECT p.id post_id, p.posted_at, p.content, a.name author_name, p.link, p.status FROM posts p left join profiles a on p.author_id = a.id", postgres_engine)
    return posts

def generate_report(processed_date):
    
    # for project_name in set(project_names):
    #     token_info.get_token_data(project_name)
    token_info = TokenInfo(ScoreSetting(),postgres_engine)
    df_project_tokens, df_category, final_token_data = token_info.generate_report(processed_date)
    st.session_state.generate_report = True
    return df_project_tokens, df_category, final_token_data        
        
    
def check_processed_result():
    processed_results = get_processed_results()
    processed_results = processed_results.loc[datetime_filter]
    if processed_results.empty:
        st.session_state.analyzed = False
    else:
        st.session_state.analyzed = True
def get_processed_results():
    processed_results = pd.read_sql("SELECT pr.*, p.posted_at  FROM processed_results pr left join posts p on pr.post_id = p.id", postgres_engine)
    return processed_results

def generate_content(final_token_data):
    if st.session_state.token_id is None:
        st.error("Please select a token to generate content.")
        return
    token_data = next(item for item in final_token_data if item["id"] == st.session_state.token_id)
    settings = ChainSetting()
    processor = PostProcessor(settings, postgres_engine)
    content = processor.generate_content(token_data)
    st.session_state.token_content = content

    

@st.fragment
def generate_content_button(final_token_data):
    content = st.button('Generate Content', on_click=generate_content,kwargs={"final_token_data":final_token_data})
    if content:
        st.session_state.token_generated = True
        st.text_area("Generated Content:",st.session_state.token_content)
@st.fragment
def token_selectbox(token_lists):
    option = st.selectbox(
                "Select token to generate content",
                options = token_lists,
                index=None,
                placeholder=  "Select token to generate content",
                on_change=None,
            )
    st.session_state.token_id = option

    # st.write(f'contact: {ss.contact}') 

if 'token_id' not in  st.session_state:
    st.session_state.token_id = None
if 'token_content' not in st.session_state:
    st.session_state.token_content = None
try:
    
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
    st.session_state.generate_report = False
    df_post = get_postgres_data()
    col1, col2 = st.columns([1,2])
    with col1:
        processed_date = st.date_input("Select a date to generate the report",value=df_post.posted_at.max(), min_value= df_post.posted_at.min(),max_value= df_post.posted_at.max())
        start_datetime = datetime.combine(processed_date, datetime.min.time())
        end_datetime = datetime.combine(processed_date, datetime.max.time())
    with col2:
        pass
    # with col3:
    #     st.button('3')

    if not processed_date:
        st.error("Please select at least one date.")
    else:
        st.subheader("Posts to be processed")
        datetime_filter = (df_post.posted_at >= start_datetime) & (df_post.posted_at <= end_datetime)
        data = df_post.loc[datetime_filter]
        available_status = data[data['status'] == 'processed']
        placeholder_post = st.empty()
        if len(available_status) >= 1:
            st.session_state.analyzed = True
        else:
            st.session_state.analyzed = False
        display_data = data[["post_id","content","author_name","posted_at"]].sort_values(by="post_id",ascending=True)
        if not st.checkbox("Hide Posts"):
            placeholder_post.dataframe(display_data,hide_index=True)
        st.subheader("1. Extract Project Name")

        placeholder_procressed = st.empty()
        if st.session_state.analyzed:
            processed_results = get_processed_results()
            datetime_filter = (processed_results.posted_at >= start_datetime) & (processed_results.posted_at <= end_datetime)
            processed_results = processed_results.loc[datetime_filter]
            #st.dataframe(processed_results)
        if not st.checkbox("Hide Processed Results"):
            processed_results = processed_results[["post_id","project_name"]].sort_values(by="post_id",ascending=True)
            placeholder_procressed.dataframe(processed_results,hide_index=True)

        report_button_clicked = st.button('Generate Report')
        if report_button_clicked:
            df_project_tokens, df_category, final_token_data  = generate_report(processed_date)
        if st.session_state.generate_report:
            #placeholder_report = st.empty()
            st.success("Report generated successfully.")
            st.subheader("2. Project Tokens")
            df_project_tokens['price_change_percentage_24h'] = df_project_tokens.apply(lambda x: f"{x['market_data']['price_change_percentage_24h']}%", axis=1)
            df_project_tokens['price_change_24h_in_usd'] = df_project_tokens.apply(lambda x: x['market_data']['price_change_24h'], axis=1)
            df_project_tokens = df_project_tokens[['symbol','price_change_percentage_24h','price_change_24h_in_usd','categories','score']].sort_values(by="score",ascending=True)
            st.dataframe(df_project_tokens)
            st.subheader("3. Categories")
            df_category = df_category[['id','name','market_cap_change_24h','top_3_coins_id']].sort_values(by="market_cap_change_24h",ascending=True)
            st.dataframe(df_category)
            st.subheader("4. Result Token Data")
            df_final_token_data = pd.DataFrame([f['market_data'] for f in final_token_data]).sort_values(by="price_change_percentage_24h",ascending=True)
            v = []
            for f in final_token_data:
                a = {
                    "id": f['id'],
                    "name": f['name'],
                    "symbol": f['symbol'],
                    "price_change_percentage_24h": f['market_data']['price_change_percentage_24h'],
                    "price_change_24h_in_usd": f['market_data']['price_change_24h'],
                    "categories": f['categories'],
                    "market_cap": f['market_data']['market_cap'],
                    "market_cap_change_24h": f['market_data']['market_cap_change_24h']
                }
                v.append(a)
            df_final_token_data = pd.DataFrame(v)
            st.dataframe(df_final_token_data)
            st.subheader("5. Generate Content")
            token_lists = [token['id'] for token in final_token_data] 
            token_selectbox(token_lists)
            generate_content_button(final_token_data)
        # st.button('Analyze posts', on_click=process_post_data)
            

        # data = data.T.reset_index()
        # data = pd.melt(data, id_vars=["index"]).rename(
        #     columns={"index": "year", "value": "Gross Agricultural Product ($B)"}
        # )
        # chart = (
        #     alt.Chart(data)
        #     .mark_area(opacity=0.3)
        #     .encode(
        #         x="year:T",
        #         y=alt.Y("Gross Agricultural Product ($B):Q", stack=None),
        #         color="Region:N",
        #     )
        # )
        # st.altair_chart(chart, use_container_width=True)
except Exception as e:

    st.error(f"An error occurred: {e}")