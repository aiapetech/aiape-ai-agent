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
    posts = pd.read_sql("SELECT p.posted_at, p.content, a.name author_name, p.link, p.status FROM posts p left join profiles a on p.author_id = a.id", postgres_engine)
    return posts

def generate_report(processed_date):
    
    # for project_name in set(project_names):
    #     token_info.get_token_data(project_name)
    token_info = TokenInfo(ScoreSetting(),postgres_engine)
    df_scrores, df_token_market_data = token_info.generate_report(processed_date)
    st.session_state.generate_report = True
    return df_scrores, df_token_market_data        
        
    
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
try:
    
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
    st.session_state.generate_report = False
    df_post = get_postgres_data()
    col1, col2 = st.columns([1,2])
    with col1:
        processed_date = st.date_input("Select a date to generate the report",value=df_post.posted_at.min(), min_value= df_post.posted_at.min(),max_value= df_post.posted_at.max())
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
        if len(available_status) > 1:
            st.session_state.analyzed = True
        else:
            st.session_state.analyzed = False
        display_data = data[["posted_at","content","author_name","link","status"]]
        
        #st.dataframe(display_data)

        if not st.checkbox("Hide Posts"):
            placeholder_post.dataframe(display_data)
        st.subheader("Processed Results")

        placeholder_procressed = st.empty()
        if st.session_state.analyzed:
            processed_results = get_processed_results()
            datetime_filter = (processed_results.posted_at >= start_datetime) & (processed_results.posted_at <= end_datetime)
            processed_results = processed_results.loc[datetime_filter]
            #st.dataframe(processed_results)
        if not st.checkbox("Hide Processed Results"):
            placeholder_procressed.dataframe(processed_results)

        report_button_clicked = st.button('Generate Report')
        if report_button_clicked:
            df_scrores, df_token_market_data = generate_report(processed_date)
        if st.session_state.generate_report:
            #placeholder_report = st.empty()
            st.success("Report generated successfully.")
            st.subheader("Token Market Data")
            st.dataframe(df_token_market_data)
            st.subheader("Scores")
            st.dataframe(df_scrores)
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