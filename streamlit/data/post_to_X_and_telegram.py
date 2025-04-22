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
from core.x import post_to_twitter_with_credentials
import time
import streamlit as st
import asyncio
from core.post_processing import ChainSetting, PostProcessor



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

def rephrase_content(content,persona=None,limit=2):
    settings = ChainSetting()
    processor = PostProcessor(settings, postgres_engine)
    if persona:
        personas = pd.read_sql(f"SELECT p.*,t.language,t.username x_username from post_personas p left join twitter_credentials t on p.twitter_app_id = t.id::TEXT where p.username = '{persona}'", postgres_engine)
    else:
        personas = pd.read_sql(f"SELECT p.*,t.language,t.username x_username from post_personas p left join twitter_credentials t on p.twitter_app_id = t.id::TEXT where p.twitter_app_id is not null order by id", postgres_engine)
    st.session_state.rephrased_content = personas.to_dict(orient='records')
    for record in  st.session_state.rephrased_content:
        record['rephrased_content'] = processor.add_persona_to_content(content, record)
    st.session_state.rephrased = True

def update_rephrased_content(username):
    for record in st.session_state.rephrased_content:
        if record['username'] == username:
            record['rephrased_content'] = st.session_state[f"{username}_content"]

def post_to_x_and_telegram(channels_option):
    telegram_bot = TelegramBot()
    #asyncio.run(telegram_bot.send_message(chat_id='addas',msg = st.session_state.rephrased_content,image_url=st.session_state.image_url))
    df_twitter_credentials = pd.read_sql(f"SELECT * from twitter_credentials", postgres_engine)
    if 'X' in channels_option:
        for record in st.session_state.rephrased_content:
            if record['posted']:
                twitter_credential = df_twitter_credentials[df_twitter_credentials.id == int(record['twitter_app_id'])].to_dict(orient='records')[0]
                res = post_to_twitter_with_credentials(record['rephrased_content'], twitter_credential['consumer_key'], twitter_credential['consumer_secret'], twitter_credential['access_token'], twitter_credential['access_secret'],media_path=record.get('image_path'))
            if not res: 
                st.error("Failed to post to X and Telegram.")
            st.success("Content posted to X successfully.")
    if 'Telegram' in channels_option:
        for record in st.session_state.rephrased_content:
            if record['posted']:
                asyncio.run(telegram_bot.send_message(chat_id='addas',msg = record['rephrased_content'],image_url=record.get('image_public_url')))
                st.success("Content posted to Telegram successfully.")
    st.session_state.posted = True
    

def is_selected(username):
    st.session_state.updated_rephrased_content[username]['posted'] != st.session_state.rephrased_content[username]['posted']


list_session_state = [
    'raw_content',
    'rephrased',
    'rephase_content_edit_box',
    'image_url',
    'posted'
]
for state in list_session_state:
    if state not in st.session_state:
        st.session_state[state] = None
if "image_urls" not in st.session_state:
    st.session_state.image_urls = []
if "rephrased_content" not in st.session_state:
    st.session_state.rephrased_content = []
raw_content = st.text_area("Please input your content",key="raw_content")
# personas = persona_list()
# 

# persona_option = st.selectbox(
#                 "Please select a persona",
#                 options = personas,
#                 index=None,
#                 placeholder="Select a persona...",
#             )

if raw_content:
    st.button('Rephrase Content', on_click=rephrase_content,
        kwargs={"content":st.session_state.raw_content,'persona':None})
# uploaded_files = st.file_uploader(
#             "Choose a images file", accept_multiple_files=False, type=["jpg", "png", "jpeg"]
#         )
# if uploaded_files:
#     upload_images(uploaded_files)
#     st.success("Images uploaded successfully.")
#     st.image(st.session_state.image_url)



if st.session_state.rephrased:
    if not raw_content:
        st.error("Please input content.")
    col1, col2, col3 = st.columns([5,5,1])
    with col1:
        st.text("Rephrased Content")
    with col2:
        st.text("Account")
    with col3:
        st.text("Select")
    for record in st.session_state.rephrased_content:
        col1, col2, col3 = st.columns([5,5,1])
        with col1:
            st.text_area(label= record['username'],value=record['rephrased_content'],key=f"{record['username']}_content",on_change=update_rephrased_content,label_visibility="hidden",kwargs={"username":record['username']})
        with col2:
            # record['image'] = st.file_uploader(
            #     record['username'],key=f"{record['username']}_images", accept_multiple_files=False, type=["jpg", "png", "jpeg"],label_visibility="hidden"
            # )
            # if record['image']:
            #     local_path, public_url = upload_images(record['image'])
            #     record['image_path'] = local_path
            #     record['image_public_url'] = public_url
            #     st.success("Images uploaded successfully.")
            #     st.image(st.session_state[f"{record['username']}_images"])
            st.text(f"https://x.com/{record['x_username'].lower()}")
        with col3:
            record['posted'] = st.checkbox("post",key=f"{record['username']}_post",label_visibility="hidden")

    selected_options = st.multiselect("Select channels to post",['Telegram','X'])
    if not selected_options:
        st.error("Please select at least one channel.")
    else:
        st.button('Post to X and Telegram', on_click=post_to_x_and_telegram,kwargs={"channels_option":selected_options})
        if st.session_state.posted:
            st.success("Content posted to X and Telegram successfully.")

    
    

