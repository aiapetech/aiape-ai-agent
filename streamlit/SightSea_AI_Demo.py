import streamlit as st

data_page = st.Page("./data/data_management.py", title="Post Management", icon=":material/add_circle:")
data_processing_page = st.Page("./data/post_processing.py", title="Post Processing", icon=":material/transform:")
report_page = st.Page("./data/report.py", title="Reports", icon=":material/insert_chart_outlined:")
pg = st.navigation([report_page])
st.set_page_config(page_title="Data management", page_icon=":material/edit:")
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
# if "messages" not in st.session_state:
#     st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])

# if prompt := st.chat_input():
#     if not openai_api_key:
#         st.info("Please add your OpenAI API key to continue.")
#         st.stop()

#     client = OpenAI(api_key=openai_api_key)
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     st.chat_message("user").write(prompt)
#     response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
#     msg = response.choices[0].message.content
#     st.session_state.messages.append({"role": "assistant", "content": msg})
#     st.chat_message("assistant").write(msg)

pg.run()
