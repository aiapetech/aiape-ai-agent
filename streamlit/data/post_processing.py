import streamlit as st
import pandas as pd
import sys, os
from pathlib import Path
CWD = Path(__file__).parents[2]
sys.path.append(str(CWD))
from core.db import engine as postgres_engine
from datetime import datetime
from core.post_processing import ChainSetting, PostProcessor


def get_postgres_data():
    posts = pd.read_sql("""SELECT p.posted_at, p.content, a.name author_name, p.link, p.status FROM posts p left join profiles a on p.author_id = a.id""", postgres_engine)
    return posts

def process_post_data():
    settings = ChainSetting()
    if option == "Google Gemini":
        settings.MODEL_PROVIDER = "google"
    else:
        settings.MODEL_PROVIDER = "openai"
    date = processed_date.strftime("%Y-%m-%d")
    processor = PostProcessor(settings, postgres_engine)
    processor.analyze_posts(date=date)
    st.session_state.clicked = True
    return True
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
    df = get_postgres_data()
    processed_results = get_processed_results()
    col1, col2 = st.columns([1,2])
    with col1:
        processed_date = st.date_input("Select a date to process the data",value=df.posted_at.max(), min_value=df.posted_at.min(), max_value=df.posted_at.max())
        start_datetime = datetime.combine(processed_date, datetime.min.time())
        end_datetime = datetime.combine(processed_date, datetime.max.time())
    with col2:
        option = st.selectbox(
                "Please select a LLM model to process the data",
                ("OpenAI", "Google Gemini"),
                index=None,
                placeholder="Select LLM model...",
            )
    # with col3:
    #     st.button('3')

    if not processed_date:
        
        st.error("Please select at least one date.")
    else:
        datetime_filter = (df.posted_at >= start_datetime) & (df.posted_at <= end_datetime)
        data = df.loc[datetime_filter]
        available_status = data[data['status'] == 'processed']
        if len(available_status) >= 1:
            st.session_state.analyzed = True
        else:
            st.session_state.analyzed = False
        display_data = data[["posted_at","content","author_name","link","status"]]
        st.subheader("Posts to be processed")
        st.dataframe(display_data)
        st.button('Analyze posts', on_click=process_post_data)

        if st.session_state.analyzed:
            st.success("Data processed successfully.")
            st.subheader("Processed Results")
            datetime_filter = (processed_results.posted_at >= start_datetime) & (processed_results.posted_at <= end_datetime)
            processed_results = processed_results.loc[datetime_filter]
            st.dataframe(processed_results)

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