import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os


def main():
    st.set_page_config(page_title="Data management", page_icon=":material/edit:")

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
    try:
        
        if st.session_state['authentication_status']:
            #authenticator.logout('main')
            data_page = st.Page("./data/data_management.py", title="Post Management", icon=":material/add_circle:")
            data_processing_page = st.Page("./data/post_processing.py", title="Post Processing", icon=":material/transform:")
            report_page = st.Page("./data/report.py", title="Reports", icon=":material/insert_chart_outlined:")
            pg = st.navigation([report_page])
            pg = st.navigation(
                    {
                        "Data": [data_page,data_processing_page],
                        "Reports": [report_page],
                    
                    }
                )
            # with st.sidebar:
            #     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")


            st.title("🤖 SightSea AI Demo")
            st.caption("🌊 AI Agent power by Zenlab 🐳")
            authenticator.logout(location='sidebar')
            pg.run()
        elif st.session_state['authentication_status'] == False:
            st.error('Username/password is incorrect')
        elif st.session_state['authentication_status'] == None:
            st.warning('Please enter your username and password')
        
        # with st.sidebar:
        #     openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

    except Exception as e:
        st.error(e)

if __name__ == '__main__':
    main()
