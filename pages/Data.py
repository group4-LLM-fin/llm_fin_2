import streamlit as st
import pandas as pd
from database.baseDatabase import Database
from database.vectorDB import VectorDB
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)

@st.cache_resource
def get_dbconn():
    user = os.getenv('USER')
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DB1')
    port = os.getenv('PORT')

    db_config = {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'dbname': dbname
    }

    vectordb = VectorDB(**db_config)
    db = Database(**db_config)
    return db, vectordb

db, vectordb = get_dbconn()

def get_data(_db: Database):
    reports = _db.read("METADATA", "reportid, bankid, year, quarter")
    banks = _db.read("BANK", "bankid, bankname, abbreviation")
    # Create DataFrames from the tuples
    reports_columns = ['reportid', 'bankid', 'year', 'quarter']
    banks_columns = ['bankid', 'abbreviation', 'bankname']

    reports_df = pd.DataFrame(reports, columns=reports_columns)
    banks_df = pd.DataFrame(banks, columns=banks_columns)
    banks_df['bankid'] = banks_df['bankid'].astype(int)

    merged_df = pd.merge(reports_df, banks_df, on="bankid")

    result_df = merged_df[["reportid", "bankname", "abbreviation", "year", "quarter"]]

    return result_df

df = get_data(_db = db)

def display_crud():
    st.title("Data Manipulation")

    st.write("Current Records:")
    header_cols = st.columns([1,1,2,1,1,1])
    header_cols[0].write("**Select**")  
    header_cols[1].write("**Report ID**")
    header_cols[2].write("**Bank Name**")
    header_cols[3].write("**Year**")
    header_cols[4].write("**Quarter**")
    header_cols[5].write("**Action**")  

    to_delete = []  

    for index, row in df.iterrows():
        cols = st.columns([1,1,2,1,1,1])  

        # Checkbox for selection
        selected = cols[0].checkbox("", key=f"checkbox_{index}")
        if selected:
            to_delete.append(row['reportid'])  # Add selected ID to the list

        cols[1].write(row['reportid'])  
        cols[2].write(row['bankname'])  
        cols[3].write(row['year'])
        cols[4].write(row['quarter'])

        # Update button
        if cols[5].button("Update", key=f"update_{index}"):
            st.session_state.selected_id = row['ID']  # Store ID for update
            st.session_state.selected_name = row['Name']  # Store name for update
            st.success(f"Ready to update {row['Name']}!")

    if st.button("Delete Selected"):
        if to_delete:
            for id in to_delete:
                st.success(f"Deleted record with ID: {id}!")
        else:
            st.warning("No records selected for deletion.")


# Display the CRUD interface
display_crud()
