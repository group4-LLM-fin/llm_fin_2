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
from OCR.readReport import readBalanceSheet, readIncome, readCashFlow
from openai import OpenAI
import fitz
from PIL import Image
from OCR.insertData import insert_all

load_dotenv()

@st.cache_resource
def get_env():
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    openai_api = os.getenv('OPENAI_API_KEY')
    voyage_api = os.getenv('VOYAGE_API')

    OpenAIembedder = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api)
    VoyageEmbedder = voyageai.Client(api_key=voyage_api)
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
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

st.title("Upload Bank Financial reports")
uploaded_file = st.file_uploader("Choose a file", type = 'pdf', accept_multiple_files = False)

if st.button("Upload"):

    if uploaded_file:
        
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        images = []

        with st.spinner("Scanning file"):
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                pix = page.get_pixmap(dpi=150)  # Set the DPI for better quality
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(image)  

        with st.spinner(text="Analyzing file..."):
            sections, metadata_text = find_table(images)
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

        with tab2:
            # Analyze Balancesheet
            with st.spinner('Read Balance Sheet...'):
                balancesheetPage = sections["Balance Sheet"]
                balancesheet = dict()
                for i in range(balancesheetPage[0], balancesheetPage[1]+1):
                    balancesheetPageInfo = readBalanceSheet(image=images[i], model=gpt)
                    balancesheet.update(balancesheetPageInfo)
            
            st.subheader("**Balance sheet:**")
            st.table(balancesheet)

        # Analyze Income statement
        with tab3:
            with st.spinner('Read Income Statement...'):
                isPage = sections["Income Statement"]
                incomestatement = dict()
                for i in range(isPage[0], isPage[1]+1):
                    isPageInfo = readIncome(image=images[i], model=gpt)
                    incomestatement.update(isPageInfo)
            
            st.subheader("**Income Statement:**")
            st.table(incomestatement)

        # Analyze Cash Flow Statement
        with tab4:
            with st.spinner('Read Cash Flow Statement...'):
                cfPage = sections["Cash Flow Statement"]
                cashflow = dict()
                for i in range(cfPage[0], cfPage[1]+1):
                    cfPageInfo = readCashFlow(image=images[i], model=gpt)
                    cashflow.update(cfPageInfo)
            
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

        