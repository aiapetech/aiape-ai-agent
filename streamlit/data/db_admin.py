import streamlit as st
import pandas as pd
import sqlalchemy as db
from sqlalchemy import inspect, text, and_, func
from sqlmodel import Session, select
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError
import os, logging, json
from core.db import engine

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App Configuration
PAGE_SIZES = [10, 20, 50, 100]


# Cache schema names to reduce repeated DB queries
@st.cache_data(ttl=None)
def get_schema_names() -> list:
  try:
    # Exclude system schemas
    query = text(
      "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema');"
    )
    ResultProxy = connection.execute(query)
    return [row[0] for row in ResultProxy.fetchall()]
  except db.exc.DatabaseError as e:
    st.error(f"Database error while getting schema names: {e}")
    logger.error(e)
    return []
  except Exception as e:
    st.error(f"Error getting schema names: {e}")
    logger.exception(e)
    return []


# Cache table names for the given schema
@st.cache_data(ttl=None)
def get_table_names(schema_name: str) -> list:
  try:
    metadata.clear()  # Clear existing metadata to avoid redundancy

    # Reflect only the specified user-defined schema
    metadata.reflect(bind=engine, schema=schema_name)

    table_names = [
      table_name.split('.')[1] for table_name in metadata.tables.keys()
      if table_name.startswith(schema_name + '.')
    ]
    return sorted(table_names)  # Sorting the table names alphabetically
  except Exception as e:
    st.error(f"Error getting table names: {e}")
    logger.exception(e)
    return []


# Retrieve paginated table data
def get_table_data(table_name: str,
                   page_number: int,
                   page_size: int = 50) -> pd.DataFrame:
  try:
    table = db.Table(table_name,
                     metadata,
                     schema=st.session_state.selected_schema,
                     autoload=True,
                     autoload_with=engine)
    query = db.select(
      table.columns).select_from(table).limit(page_size).offset(page_number *
                                                                page_size)
    ResultProxy = connection.execute(query)
    return pd.DataFrame(ResultProxy.fetchall(), columns=ResultProxy.keys())
  except Exception as e:
    st.error(f"Error getting table data: {e}")
    logger.exception(e)
    return pd.DataFrame()


# Update the specified table with edited data using a transaction
def update_table_data(table_name: str, original_df: pd.DataFrame,
                      edited_df: pd.DataFrame):
  try:
    table = db.Table(table_name,
                     metadata,
                     schema=st.session_state.selected_schema,
                     autoload=True,
                     autoload_with=engine)
    with connection.begin() as trans:
      for index, original_row in original_df.iterrows():
        edited_row = edited_df.loc[index]
        if original_row.equals(edited_row):
          continue
        update_values = edited_row.to_dict()
        primary_key_columns = [key.name for key in inspect(table).primary_key]
        primary_key_conditions = [
          getattr(table.c, col) == original_row[col]
          for col in primary_key_columns
        ]
        connection.execute(table.update().where(
          and_(*primary_key_conditions)).values(update_values))
      trans.commit()
    st.success("Data updated successfully!")
  except db.exc.DatabaseError as e:
    st.error(f"Database error while updating table data: {e}")
    logger.error(e)
  except Exception as e:
    st.error(f"Error updating table data: {e}")
    logger.exception(e)


def truncate_records(schema_name):
  table_names = get_table_names(schema_name)
  for table_name in table_names:
    if table_name != 'user':
      query = text(f"TRUNCATE TABLE {schema_name}.{table_name};")
      connection.execute(query)
  st.success(f"Truncated all tables in {schema_name} except for 'user' table.")


def drop_all_tables(schema_name):
  table_names = get_table_names(schema_name)
  for table_name in table_names:
    query = text(f"DROP TABLE IF EXISTS {schema_name}.{table_name};")
    connection.execute(query)
  st.success(f"Dropped all tables in {schema_name}.")


def export_db_schema(schema_name):
  table_data = []
  table_names = get_table_names(schema_name)
  for table_name in table_names:
    table = db.Table(table_name,
                     metadata,
                     autoload_with=engine,
                     schema=schema_name)
    columns = [(col.name, str(col.type)) for col in table.columns]
    table_data.append((table_name, columns))
  st.write(f"Schema export for {schema_name}:", table_data)


def export_db_json(schema_name):
  db_json = {}
  table_names = get_table_names(schema_name)
  for table_name in table_names:
    table = db.Table(table_name,
                     metadata,
                     autoload_with=engine,
                     schema=schema_name)
    columns = [col.name for col in table.columns]
    db_json[table_name] = columns
  st.write(f"JSON export for {schema_name}:", json.dumps(db_json, indent=2))


# Streamlit app interface
st.title("StreamlitDBAdmin")

# Connect to your SQL database with connection pooling

try:
  connection = Session(engine)
except OperationalError as e:
  if "FATAL:  password authentication failed" in str(e):
    st.error("Password authentication failed, please check your credentials.")
    logger.exception(e)
    # Optionally, you could add logic here to prompt the user for new credentials or take other appropriate action.
  else:
    st.error("An unexpected error occurred while connecting to the database.")
    logger.exception(e)

  st.stop()

metadata = db.MetaData()
inspector = inspect(engine)

st.sidebar.title("Settings")

# Utilize st.session_state to maintain selected schema and table across interactions
if 'selected_schema' not in st.session_state:
  st.session_state.selected_schema = get_schema_names()[0]
if 'selected_table' not in st.session_state:
  st.session_state.selected_table = get_table_names(
    st.session_state.selected_schema)[0]

# Allow selection of schema and table
st.session_state.selected_schema = st.sidebar.selectbox(
  "Select a schema:", get_schema_names())
st.session_state.selected_table = st.sidebar.selectbox(
  "Select a table:", get_table_names(st.session_state.selected_schema))

# Available page sizes
page_size = st.sidebar.selectbox("Page size:", PAGE_SIZES, index=2)

# Display and edit the selected table
if st.session_state.selected_table:
  table = db.Table(st.session_state.selected_table,
                   metadata,
                   autoload_with=engine,
                   schema=st.session_state.selected_schema)
  stmt = select(func.count()).select_from(table)
  result = connection.execute(stmt)
  total_rows = result.scalar()

  if total_rows > 0:
    total_pages = (total_rows + page_size - 1) // page_size
    page_numbers = range(total_pages)
    page_number = st.sidebar.selectbox("Page number:", page_numbers)

    table_data = get_table_data(st.session_state.selected_table, page_number,
                                page_size)
    edited_data = st.data_editor(table_data, num_rows="dynamic")

    if edited_data is not table_data:
      if st.button('Save Changes'):
        update_table_data(st.session_state.selected_table, table_data,
                          edited_data)
  else:
    st.warning("The selected table contains no data.")

# Additional buttons for new features
selected_schema = st.session_state.selected_schema

st.sidebar.subheader("Database Administration")
if st.sidebar.button("Export DB Schema"):
  export_db_schema(selected_schema)

if st.sidebar.button("Export DB JSON"):
  export_db_json(selected_schema)

st.sidebar.subheader("Danger Zone")
if st.sidebar.button("Truncate Records from Tables"):
  if st.sidebar.checkbox(
      f"WARNING: You are about to truncate all tables except 'user' in the '{selected_schema}' schema. Confirm?"
  ):
    truncate_records(selected_schema)

if st.sidebar.button("Drop All Tables"):
  if st.sidebar.checkbox(
      f"WARNING: You are about to drop all tables in the '{selected_schema}' schema. Confirm?"
  ):
    drop_all_tables(selected_schema)