import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path
CWD = Path(__file__).parents[2]
sys.path.append(str(CWD))
from core.db import engine
from sqlalchemy import create_engine
from datetime import datetime


@st.cache_data
def get_posts_data():
    posts = pd.read_sql("SELECT p.posted_at, p.content, a.name author_name, p.link FROM posts p left join profiles a on p.author_id = a.id", engine)
    return posts
@st.cache_data
def get_profiles():
    profiles = pd.read_sql("SELECT * FROM profiles", engine)
    return profiles
try:
    #st.session_state['authentication_status'] = True
    df_post = get_posts_data()
    df_profile = get_profiles()
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        start_date = st.date_input("Select start date", df_post.posted_at.min(), df_post.posted_at.max())
        start_datetime = datetime.combine(start_date, datetime.min.time())
    with col2:
        end_date = st.date_input("Select end date", df_post.posted_at.min(), df_post.posted_at.max())
        end_datetime = datetime.combine(end_date, datetime.max.time())
    # with col3:
    #     st.button('3')

    if not start_date or not end_date:
        st.error("Please select at least one date.")
    else:
        datetime_filter = (df_post.posted_at >= start_datetime) & (df_post.posted_at <= end_datetime)
        data = df_post.loc[datetime_filter]
        display_data = data[["posted_at","content","author_name","link"]]
        st.subheader("Posts")
        st.dataframe(display_data)
        st.subheader("Authors")
        st.dataframe(df_profile[["name","link"]])
except Exception as e:

    st.error(f"An error occurred: {e}")