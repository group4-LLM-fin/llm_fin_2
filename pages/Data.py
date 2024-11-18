import streamlit as st
import pandas as pd
from database.baseDatabase import Database
from database.vectorDB import VectorDB
import os
from dotenv import load_dotenv

load_dotenv(override=True)

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

@st.dialog("Warning")
def delete():
    st.write(f"Are you sure you want to delete the selected records: {st.session_state.to_delete}")
    col1, col2 = st.columns([1,1])

    with col1:
        delet = st.button('Delete')
    with col2:
        cance = st.button('Cancel')

    if delet:
        try:
            for id in st.session_state.to_delete:
                db.delete(table_name="INCOMESTATEMENT", conditions={'reportid': id})
                db.delete(table_name="CASHFLOW", conditions={'reportid': id})
                db.delete(table_name="BALANCESHEET", conditions={'reportid': id})
                db.delete(table_name="METADATA", conditions={'reportid': id})
            # Reset states after deletion
            st.session_state.delete_triggered = False
            st.session_state.to_delete = []
            st.rerun()
        except Exception as e:
            st.error(e)
    if cance:
        st.session_state.delete_triggered = False
        st.rerun()
        

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

# Initialize session states for tracking deletions and confirmations
if 'delete_triggered' not in st.session_state:
    st.session_state.delete_triggered = False
if 'to_delete' not in st.session_state:
    st.session_state.to_delete = []

# Load data
df = get_data(_db=db)

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

    # Clear selected records for deletion
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
            st.session_state.selected_id = row['reportid']
            st.session_state.selected_name = row['bankname']
            st.success(f"Ready to update {row['bankname']}!")

    # If the "Delete Selected" button is clicked, set confirmation trigger
    del_butt = st.button("Delete Selected", disabled=True)
    if del_butt:
        if to_delete:
            st.session_state.delete_triggered = True
            st.session_state.to_delete = to_delete
        else:
            st.warning("No records selected for deletion.")

    # Display confirmation dialog if delete_triggered is True
    if st.session_state.delete_triggered:
        delete()

# Display the CRUD interface
display_crud()
