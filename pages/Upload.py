import streamlit as st
from langchain.embeddings import OpenAIEmbeddings
from database.vectorDB import VectorDB
from dotenv import load_dotenv
import os
import pytesseract
from database.baseDatabase import Database
import voyageai
from OCR.analyzeReport import find_table, get_metadata
import pandas as pd
import google.generativeai as genai
from openai import OpenAI
import fitz
from PIL import Image
from OCR.insertData import insert_all
from utils.pallelize_reading import *
import concurrent.futures

load_dotenv(override=True)

st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)   

@st.cache_resource
def get_env():
    # try:
    #     tesseract_dir = os.getenv('TESSERACT')
    #     pytesseract.pytesseract.tesseract_cmd = tesseract_dir
    # except:
    pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
    openai_api = os.getenv('OPENAI_API_KEY')
    voyage_api = os.getenv('VOYAGE_API')
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    OpenAIembedder = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api)
    VoyageEmbedder = voyageai.Client(api_key=voyage_api)
    gemini = genai.GenerativeModel("gemini-1.5-pro")
    gpt = OpenAI(api_key=openai_api)

    return OpenAIembedder, VoyageEmbedder, gemini, gpt

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

@st.cache_data
def get_bankName(_db):
    banks = _db.read("BANK", "bankname, abbreviation, bankid")
    sorted_banks = sorted(banks, key=lambda x: x[-1])
    banks_name = [f"{bank[0]} ({bank[1]})" for bank in sorted_banks]
    bankid = [bank[-1] for bank in sorted_banks]
    return banks_name, bankid

db, vectordb = get_dbconn()
banks_name, bankid = get_bankName(db)
openaiEmbeeder, voyageEmbedder, gemini, gpt = get_env()

col1, col2 = st.columns([1, 3]) 

# Title in the first column
with col1:
    st.image(r"graphics\logo.png", use_container_width=True)

with col2:
    st.markdown("<h1 style='text-align: left;'>Upload Bank Financial Reports</h1>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose a file", type = 'pdf', accept_multiple_files = False)

if st.button("Upload"):
    
    if uploaded_file:
        progress_bar = st.progress(0,"Scanning file...")
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        images = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            pix = page.get_pixmap(dpi=200)  # Set the DPI for better quality
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(image)  
            progress_bar.progress(page_num+1, "Scanning file...")
        progress_bar.empty()

        with st.spinner(text="Analyzing file..."):
            sections, metadata_text, explaination_part = find_table(images)
            sections_df = pd.DataFrame.from_dict(sections, orient='index', columns=['Start Page', 'End Page'])
            sections_df['Start Page'] += 1
            sections_df['End Page'] += 1

        # Display section info
        st.subheader("**Section Information:**")
        st.table(sections_df)

        tab1, tab2, tab3, tab4 = st.tabs(["Metadata", "Balance Sheet", "Income Statement", "Cash Flow"])

        with tab1:
            # Analyze metadata
            with st.spinner(text="Getting metadata"):
                metadata = get_metadata(extracted_text= metadata_text, model = gemini)
                
                metadata_df = dict()
                # Find bank name
                for i in range(len(bankid)):
                    if str(bankid[i]) == str(metadata['bankid']):
                        metadata_df['Bank'] = banks_name[i]
                        break
                metadata_df['Symbol'] = metadata['banksymbol']
                metadata_df['Bank CITAD Id'] = metadata['bankid']
                metadata_df['Year'] = metadata['year']
                metadata_df['Quarter'] = metadata['quarter']

            st.subheader("**Report data:**")
            st.table(metadata_df)

        # Run each section in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tab2_future = executor.submit(process_balancesheet, images, sections["Balance Sheet"], gpt, metadata)
            tab3_future = executor.submit(process_incomestatement, images, sections["Income Statement"], gpt, metadata)
            tab4_future = executor.submit(process_cashflow, images, sections["Cash Flow Statement"], gpt, metadata)

        with tab2:
            with st.spinner('Read Balance Sheet...'):
                balancesheet = tab2_future.result()
            st.subheader("**Balance Sheet:**")
            st.table(balancesheet)

        with tab3:
            with st.spinner('Read Income Statement...'):
                incomestatement = tab3_future.result()
            st.subheader("**Income Statement:**")
            st.table(incomestatement)

        with tab4:
            with st.spinner('Read Cash Flow Statement...'):
                cashflow = tab4_future.result()
            st.subheader("**Cash Flow Statement:**")
            st.table(cashflow)
        
        # Upload to database
        with st.spinner('Upload your fiancial statement...'):
            try:
                insert_all(
                    metadata=metadata,
                    bs = balancesheet,
                    ics= incomestatement,
                    cf = cashflow,
                    vectordb= vectordb,
                    db = db
                )
                st.success('Upload your report successfully')
            
            except Exception as e:
                raise e

        