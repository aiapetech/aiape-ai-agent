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
from core.mongodb import init_mongo
from core.qa_chat import QARetriver 
import time
from core.x import post_to_twitter

mongo_client = init_mongo()
mongo_client_db = mongo_client['sightsea'] 


def get_postgres_data():
    posts = pd.read_sql("SELECT p.id post_id, p.posted_at, p.content, a.name author_name, p.link, p.status FROM posts p left join profiles a on p.author_id = a.id", postgres_engine)
    return posts

def get_mongo_x_post():
    full_data_posts = mongo_client_db.posts.find({})
    displayed_posts = []
    for post in full_data_posts:
        displayed_posts.append(
            {
            "post_id": post['id'],
            "content": post['text'],
            "author_name": post['author']['userName'],
            "posted_at": post['createdAt']}
        )
    df_post = pd.DataFrame(displayed_posts) 
    return df_post

def extract_most_mentioned_project_name():
    settings = ChainSetting()
    post_processor = PostProcessor(settings, postgres_engine)
    df_project_name = post_processor.extract_project_name_mongo()
    df_project_name.sort_values(by="ai_logic_count",ascending=False).reset_index(drop=True,inplace=True)
    st.session_state.project_name_extraction = True
    st.session_state.df_project_name = df_project_name
    st.success("Project name extracted successfully.")


def generate_report(processed_date):
    
    # for project_name in set(project_names):
    #     token_info.get_token_data(project_name)
    token_info = TokenInfo(ScoreSetting(),postgres_engine)
    df_project_tokens, df_category, df_potential_tokens = token_info.generate_report_v2(processed_date)
    st.session_state.generate_report = True
    return df_project_tokens, df_category, df_potential_tokens        
        
    
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
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def generate_content():
    if st.session_state.token_id is None:
        st.error("Please select a token to generate content.")
        return
    settings = ScoreSetting()
    token_info = TokenInfo(settings,postgres_engine)
    token_data = token_info.get_token_info(st.session_state.token_id)
    settings = ChainSetting()
    processor = PostProcessor(settings, postgres_engine)
    content = processor.generate_content(token_data)
    st.session_state.qa_token_content = content
    return True

    
def generate_x_post(final_token_data):
    settings = ScoreSetting()
    token_info = TokenInfo(settings,postgres_engine)
    st.session_state.token_content= []
    for token in final_token_data:
        tokendata = token_info.get_token_info(token['id'])
        settings = ChainSetting()
        processor = PostProcessor(settings, postgres_engine)
        content = processor.generate_content(tokendata)
        st.session_state.token_content.append(content)
    return True

def post_to_x(content):
    post_to_twitter(content)
    return True

@st.fragment
def generate_x_content_button(final_token_data):
    content = st.button('Generate X Post', on_click=generate_x_post,kwargs={"final_token_data":final_token_data[:2]})
    if content:
        token_1 = final_token_data[0]
        token_2 = final_token_data[1]
        st.session_state.potential_post = True
        st.text_area(f"Post for {token_1['name'].upper()}:",st.session_state.token_content[0])
        result_1 = st.button(f"Post to X for {token_1['name']}", on_click=post_to_x,kwargs={"content":st.session_state.token_content[0]})
        if result_1:
            st.success(f"Post for {token_1['name']} posted successfully.")
        
        st.text_area(f"Post for {token_2['name'].upper()}:",st.session_state.token_content[1])
        result_2 = st.button(f"Post to X for {token_2['name']}", on_click=post_to_x,kwargs={"content":st.session_state.token_content[1]})
        if result_2:
            st.success(f"Post for {token_2['name']} posted successfully.")

@st.fragment
def generate_content_button():
    content = st.button('Generate Content', on_click=generate_content)
    if content:
        response = st.write_stream(response_generator(st.session_state.qa_token_content))
        #st.text_area("Answer:",st.session_state.qa_token_content)
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
if 'df_project_name' not in st.session_state:
    st.session_state.df_project_name = None
if 'token_id' not in  st.session_state:
    st.session_state.token_id = None
if 'token_content' not in st.session_state:
    st.session_state.token_content = []
if 'project_name_extraction' not in st.session_state:
    st.session_state.project_name_extraction = None
if 'generate_report' not in st.session_state:
    st.session_state.generate_report = None
if 'qa_token_content' not in st.session_state:
    st.session_state.qa_token_content = None

try:
    
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
    st.session_state.generate_report = False
    #df_post = get_postgres_data()
    df_post = get_mongo_x_post()
    # col1, col2 = st.columns([1,2])
    # with col1:
    #     processed_date = st.date_input("Select a date to generate the report",value=df_post.posted_at.max(), min_value= df_post.posted_at.min(),max_value= df_post.posted_at.max())
    #     start_datetime = datetime.combine(processed_date, datetime.min.time())
    #     end_datetime = datetime.combine(processed_date, datetime.max.time())
    # with col2:
    #     pass
    # with col3:
    #     st.button('3')

    # if not processed_date:
    #     st.error("Please select at least one date.")
    #else:
        # st.subheader("Posts to be processed")
        # datetime_filter = (df_post.posted_at >= start_datetime) & (df_post.posted_at <= end_datetime)
        # data = df_post.loc[datetime_filter]
        #available_status = data[data['status'] == 'processed']
    placeholder_post = st.empty()
    # if len(available_status) >= 1:
    #     st.session_state.analyzed = True
    # else:
    #     st.session_state.analyzed = False
    display_data = df_post[["post_id","content","author_name","posted_at"]].sort_values(by="post_id",ascending=True)
    if not st.checkbox("Hide Posts"):
        placeholder_post.dataframe(display_data,hide_index=True)
    extracted_button_clicked = st.button('1-Extract top most mentioned project name')
    if extracted_button_clicked:
        extract_most_mentioned_project_name()
       
    if st.session_state.project_name_extraction:
        st.subheader("1. Top most mentioned projects in X")
        placeholder_procressed = st.empty()
        placeholder_procressed.dataframe(st.session_state.df_project_name[['project_id','name','symbol']])
        report_button_clicked = st.button('2-Generate AI Report')
        if report_button_clicked:
            df_project_tokens, df_category, df_potential_tokens  = generate_report(st.session_state.df_project_name)
            

    if st.session_state.generate_report:
        #placeholder_report = st.empty()
        st.success("Report generated successfully.")
        st.subheader("2. Find out hot project tokens")
        df_project_tokens['price_change_percentage_24h'] = df_project_tokens.apply(lambda x: f"{x['market_data']['price_change_percentage_24h']}%", axis=1)
        df_project_tokens['market_cap_change_percentage_24h'] = df_project_tokens.apply(lambda x: x['market_data']['market_cap_change_percentage_24h'], axis=1)
        df_project_tokens = df_project_tokens[['symbol','price_change_percentage_24h','market_cap_change_percentage_24h','categories','score']].sort_values(by="score",ascending=False)
        st.dataframe(df_project_tokens,hide_index=True)
        st.subheader("3. Extract category data from hot project tokens")
        df_category = df_category[['id','name','market_cap_change_24h','top_3_coins_id']].sort_values(by="market_cap_change_24h",ascending=False)
        st.dataframe(df_category,hide_index=True)
        st.subheader("4. Find out next potential tokens")
        # final_token_data = df_potential_tokens.to_dict('records')
        # #df_final_token_data = pd.DataFrame([f['market_data'] for f in final_token_data]).sort_values(by="score",ascending=True)
        # v = []
        # for f in final_token_data:
        #     a = {
        #         "id": f['id'],
        #         "name": f['name'],
        #         "symbol": f['symbol'],
        #         "price_change_percentage_24h": f['market_data']['price_change_percentage_24h'],
        #         "price_change_24h_in_usd": f['market_data']['price_change_24h'],
        #         "categories": f['categories'],
        #         "market_cap": f['market_data']['market_cap'],
        #         "market_cap_change_24h": f['market_data']['market_cap_change_24h']
        #     }
        #     v.append(a)
        # df_final_token_data = pd.DataFrame(v)
        st.dataframe(df_potential_tokens,hide_index=True)
        st.subheader("5. Generate Content")

        token_lists = df_potential_tokens.id.to_list()
        potential_tokens = df_potential_tokens.to_dict('records')[:2]
        generate_x_content_button(potential_tokens)
        token_selectbox(token_lists)
        generate_content_button()
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