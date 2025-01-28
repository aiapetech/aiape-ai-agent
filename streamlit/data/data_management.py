import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path
CWD = Path(__file__).parents[2]
sys.path.append(str(CWD))
from core.db import engine
from models.postgres_models import Posts, Profiles
from sqlalchemy import create_engine
from datetime import datetime
from sqlmodel import Session
from sqlalchemy import text



@st.cache_data
def get_posts_data():
    posts = pd.read_sql("SELECT p.posted_at, p.content, a.name author_name, p.link FROM posts p left join profiles a on p.author_id = a.id", engine)
    return posts
@st.cache_data
def get_profiles():
    profiles = pd.read_sql("SELECT * FROM profiles", engine)
    return profiles
def profile_submitted():
    st.session_state['profile_form_intput']=True
    st.session_state.profile_submitted = True
def post_submitted():
    st.session_state['post_form_intput']= True
    st.session_state.post_submitted = True
def insert_post(content, link, author_id, posted_at):
    with Session(engine) as session:
        post = Posts(content=content, link=link, author_id=author_id, posted_at=posted_at)
        session.add(post)
        session.commit()
    return True

def insert_profile(name, link):
    with Session(engine) as session:
        profile = Profiles(channel_id=1,name=name, link=link) 
        session.add(profile)
        session.commit()
    return True
try:
    #st.session_state['authentication_status'] = True
    df_post = get_posts_data()
    df_profile = get_profiles()
    col1, col2, col3 = st.columns([1,1,1])
    # st.session_state['profile_form_intput']=False
    # st.session_state['post_form_intput']=False
    # st.session_state.profile_submitted = False
    # st.session_state.post_submitted = False
    prpfile_submit = False
    with col1:
        start_date = st.date_input("Select start date",value=df_post.posted_at.min(), min_value =df_post.posted_at.min(), max_value = df_post.posted_at.max(),on_change=st.rerun)
        start_datetime = datetime.combine(start_date, datetime.min.time())
    with col2:
        end_date = st.date_input("Select end date",value=df_post.posted_at.max(), min_value =df_post.posted_at.min(), max_value = df_post.posted_at.max(),on_change=st.rerun)
        end_datetime = datetime.combine(end_date, datetime.max.time())
    # with col3:
    #     st.button('3')

    if not start_date or not end_date:
        st.error("Please select at least one date.")
    else:
        st.subheader("Authors")
        st.dataframe(df_profile[["id","name","link"]])
        if st.button('Add New Profile'):
            st.session_state['profile_form_intput']=True
        if ("profile_form_intput" in st.session_state) and st.session_state['profile_form_intput']:
            with st.form(key='new_profile_form',enter_to_submit=False,clear_on_submit=True):
                profile_name = st.text_input('Name',key='new_profile_name')
                profile_link = st.text_input('Link',key='new_profile_link')
                profile_submit = st.form_submit_button(label='Submit',on_click=profile_submitted)
        if 'profile_submitted' in st.session_state:
            if st.session_state.profile_submitted:
                res = insert_profile(st.session_state.new_profile_name, st.session_state.new_profile_link)
                if res:
                    st.success('Profile added successfully!')
                    st.success('Please refresh the page to see the updated data')
                else:
                    st.error('Error adding post')
                st.session_state['profile_form_intput']=False
                st.session_state.profile_submitted = False

        datetime_filter = (df_post.posted_at >= start_datetime) & (df_post.posted_at <= end_datetime)
        data = df_post.loc[datetime_filter]
        display_data = data[["posted_at","content","author_name","link"]]
        st.subheader("Posts")
        st.dataframe(display_data)
        if st.button('Add New Post'):
            st.session_state['post_form_intput']=True
        if ("post_form_intput" in st.session_state) and (st.session_state['post_form_intput']):
            with st.form(key='new_post_form',enter_to_submit=False,clear_on_submit=True):
                content = st.text_input('Content',key='new_post_content')
                link = st.text_input('Link',key='new_post_link')
                author_id = st.number_input('Author ID', min_value=1, step=1,key='new_post_author_id')
                col_form1, col_form2, = st.columns([1,1])
                with col_form1:
                    posted_date = st.date_input('Posted Date', datetime.now())
                with col_form2:
                    posted_time = st.time_input('Posted Time', datetime.now().time())
                st.session_state.new_posted_at = datetime.combine(posted_date, posted_time)
                post_submit_button = st.form_submit_button(label='Submit',on_click=post_submitted)
        if "post_submitted" in st.session_state:
            if st.session_state.post_submitted:
                res = insert_post(st.session_state.new_post_content, st.session_state.new_post_link, st.session_state.new_post_author_id, st.session_state.new_posted_at)
                if res:
                    st.success('Post added successfully!')
                    st.success('Please refresh the page to see the updated data')
                else:
                    st.error('Error adding post')
                st.session_state['post_form_intput']=False
                st.session_state.post_submitted = False
except Exception as e:

    st.error(f"An error occurred: {e}")