from openai import OpenAI
import streamlit as st
import pandas as pd
from core.db import engine as postgres_engine
from core.post_processing import ChainSetting
from core.qa_chat import QARetriver 
from core.digital_ocean import DigitalOceanClient
from core.telegram_bot import TelegramBot
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
    

def persona_list():
    persona = pd.read_sql("SELECT * from post_personas", postgres_engine)
    return persona.username.values.tolist()

def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def rephrase_content(content,persona):
    settings = ChainSetting()
    processor = PostProcessor(settings, postgres_engine)
    persona = pd.read_sql(f"SELECT * from post_personas where username = '{
        persona}'", postgres_engine)
    persona_content = persona.to_dict(orient='records')[0]
    st.session_state.rephrased_content = processor.add_persona_to_content(content, persona_content)
    st.session_state.rephrased = True

def update_rephrased_content():
    if st.session_state.updated_rephrased_content != st.session_state.rephrased_content:
        st.session_state.rephrased_content = st.session_state.updated_rephrased_content

def post_to_x_and_telegram():
    telegram_bot = TelegramBot()
    st.session_state.rephrased_content = st.session_state.updated_rephrased_content
    asyncio.run(telegram_bot.send_message(chat_id='addas',msg = st.session_state.rephrased_content,image_url=st.session_state.image_url))
    st.session_state.posted = True
    st.success("Content posted to X and Telegram successfully.")

list_session_state = [
    'raw_content',
    'rephrased',
    'rephase_content_edit_box',
    'image_url',
    'posted',
    'rephrased_content'
]
for state in list_session_state:
    if state not in st.session_state:
        st.session_state[state] = None
if "image_urls" not in st.session_state:
    st.session_state.image_urls = []
personas = persona_list()
raw_content = st.text_input("Please input your content",key="raw_content")

persona_option = st.selectbox(
                "Please select a persona",
                options = personas,
                index=None,
                placeholder="Select a persona...",
            )

if raw_content:
    st.button('Rephrase Content', on_click=rephrase_content,
        kwargs={"content":st.session_state.raw_content,'persona':persona_option})
uploaded_files = st.file_uploader(
            "Choose a images file", accept_multiple_files=False, type=["jpg", "png", "jpeg"]
        )
if uploaded_files:
    upload_images(uploaded_files)
    st.success("Images uploaded successfully.")
    st.image(st.session_state.image_url)
    
if st.session_state.rephrased:
    if not raw_content:
        st.error("Please input content.")
    if not persona_option:
        st.error("Please select a persona.")
    
    rephase_content_edit_box = st.text_input("Rephrased Content", value=st.session_state.rephrased_content,key="updated_rephrased_content", on_change=update_rephrased_content)
    selected_options = st.multiselect("Select channels to post",
    ['Telegram','X'])
    st.button('Post to X and Telegram', on_click=post_to_x_and_telegram)

    
    

