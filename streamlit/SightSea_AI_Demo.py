import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os


    

# st.session_state['authentication_status'] = True
# try:
    
#     if st.session_state['authentication_status']:
#         #authenticator.logout('main')
#         data_page = st.Page("./data/data_management.py", title="Post Management", icon=":material/add_circle:")
#         data_processing_page = st.Page("./data/post_processing.py", title="Post Processing", icon=":material/transform:")
#         report_page = st.Page("./data/report.py", title="Reports", icon=":material/insert_chart_outlined:")
#         pg = st.navigation([report_page])
#         pg = st.navigation(
#                 {
#                     "Data": [data_page,data_processing_page],
#                     "Reports": [report_page],
                
#                 }
#             )
#         # with st.sidebar:
#         #     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")


#         st.title("🤖 SightSea AI Demo")
#         st.caption("🌊 AI Agent power by Zenlab 🐳")
#         authenticator.logout(location='sidebar')
#         pg.run()
#     elif st.session_state['authentication_status'] == False:
#         st.error('Username/password is incorrect')
#     elif st.session_state['authentication_status'] == None:
#         st.warning('Please enter your username and password')
    
#     # with st.sidebar:
#     #     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

# except Exception as e:
#     st.error(e)
st.set_page_config(page_title="SightSea-AI-Demo", page_icon=":material/edit:")
    
if "authenticated" not in st.session_state:
    cwd = os.getcwd()
    with open(f'{cwd}/authentication.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    authenticator.login()
    if st.session_state['authentication_status'] == False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] == None:
        st.warning('Please enter your username and password')
   
#data_page = st.Page("./data/data_management.py", title="1. Import post", icon=":material/add_circle:")
#data_processing_page = st.Page("./data/post_processing.py", title="2. Analyze post", icon=":material/transform:")
report_page = st.Page("./data/report_v2.py", title="1. AI Report Generator", icon=":material/insert_chart_outlined:")#
qa_page = st.Page("./data/qa.py", title="2. Q&A", icon=":material/transform:")#
post_to_telegram_x = st.Page("./data/post_to_X_and_telegram.py", title="3. Post to Telegram and X", icon=":material/dataset:")#
liquidity_bot_page = st.Page("./data/liquidity_bot.py", title="4. Liquidity Bot", icon=":material/dataset:")#

#db_admin = st.Page("./data/db_admin.py", title="DB Admin", icon=":material/insert_chart_outlined:")

#pg = st.navigation([report_page])
if st.session_state['authentication_status'] == True:
    pg = st.navigation(
            {
                #"Data": [
                        #db_admin,
                        #data_page,
                        #data_processing_page],
                "Reports": [report_page,qa_page,post_to_telegram_x,liquidity_bot_page],
            
            }
        )

# with st.sidebar:
#     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

    st.title("🤖 SightSea AI Demo")
    st.caption("🌊 AI Agent powered by SightSea AI team 🐳")
    authenticator.logout(location='sidebar')
    pg.run()    