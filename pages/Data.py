import streamlit as st
from langchain.embeddings import OpenAIEmbeddings
from database.vectorDB import VectorDB
from dotenv import load_dotenv
import os
import fitz
from pdf2image import convert_from_path
from unidecode import unidecode
import numpy as np
import pandas as pd
load_dotenv()
pytesseract.pytesseract.tesseract_cmd = r"D:\TesereactOCR\tesseract.exe"
openai_api = os.getenv('OPENAI_API_KEY')

embedder = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api)

def find_table(pdf_path):
    # images = convert_from_path(pdf_path, dpi=300)
    pdf_document = fitz.open(pdf_path)

    signals = {
        1: ('balance sheet', ['tien mat', 'vang', 'da quy']),
        2: ('income statement', ['thu nhap lai thuan']),
        3: ('cash flow', ['luu chuyen tien']),
        4: ('thuyet minh', ['don vi bao cao', 'dac diem hoat dong']),
    }
    thuyet_minh_part = []
    result = [np.nan] * pdf_document.page_count
    k = 1

    for i, page_number in enumerate(range(pdf_document.page_count)):  # Use enumerate to get index i
        page = pdf_document[page_number]
        
        # Chuyển đổi trang thành ảnh với độ phân giải 150 DPI
        pix = page.get_pixmap(dpi=150)

        # Convert fitz.Pixmap to PIL.Image.Image
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        text = pytesseract.image_to_string(image, lang='vie')  # Pass PIL image to pytesseract
        test_text = unidecode(text.lower())

        if k in signals:
            label, current_signals = signals[k]
            if any(signal in test_text for signal in current_signals):
                result[i] = k
                k += 1
            else:
                result[i] = result[i-1] if i > 0 else np.nan
        else:
            result[i] = result[i-1] if i > 0 else np.nan

        if result[i] == 4:
            first_half, second_half = split_text_by_sentences(text)
            embedding1 = embedder.embed_documents(texts=first_half)
            embedding1 = embedding1[0]
            embedding2 = embedder.embed_documents(texts=second_half)
            embedding2 = embedding2[0]
            db.insert_embedding(
                table_name="EXPLANATION",
                bank = bank,
                year = year,
                quarter = quarter, 
                text = first_half, 
                page = i, 
                part = 1, 
                Embedding = embedding1
            )
            db.insert_embedding(
                table_name="EXPLANATION",
                bank = bank,
                year = year,
                quarter = quarter, 
                text = second_half, 
                page = i, 
                part = 2, 
                Embedding = embedding2
            )
            
    result_filled = pd.Series(result).map({1: 'balance sheet', 2: 'income statement', 3: 'cash flow', 4: 'thuyet minh'}).fillna('muc luc').tolist()
    
    # Logging each section range for display
    sections = {
        "Muc Luc": (0, result_filled.index('balance sheet') - 1),
        "Balance Sheet": (result_filled.index('balance sheet'), result_filled.index('income statement') - 1),
        "Income Statement": (result_filled.index('income statement'), result_filled.index('cash flow') - 1),
        "Cash Flow": (result_filled.index('cash flow'), result_filled.index('thuyet minh') - 1),
        "Thuyet Minh": (result_filled.index('thuyet minh'), len(result_filled) - 1)
    }

    return sections

def split_text_by_sentences(text):
    sentences = text.split('. ')
    midpoint = len(sentences) // 2
    first_half = '. '.join(sentences[:midpoint]) + '.'
    second_half = '. '.join(sentences[midpoint:])
    return first_half, second_half

st.title("Page 2")
st.write("You can upload your file here!")


load_dotenv()

user = os.getenv('USER')
host = os.getenv('HOST')
port = os.getenv('PORT')
password = os.getenv('PASSWORD')
dbname = os.getenv('DB1')

del os.environ["PORT"]

port = os.getenv('PORT')

db_config = {
    'user': user,
    'password': password,
    'host': host,
    'port': port,
    'dbname': dbname
}

db = VectorDB(**db_config)

uploaded_file = st.file_uploader("Choose a file", type = 'pdf', accept_multiple_files = False)

st.write("Financial Statement Information ")


bank = st.text_input("Enter your bank:")


year = st.number_input("Enter your year:", min_value=2000, max_value=2024, step=1)


quarter = st.selectbox("Enter your quarter (optional):", options=["None", 1, 2, 3, 4])

if st.button("Submit"):
    st.write("**Bank:**", bank)
    st.write("**Year:**", year)
    st.write("**Quarter:**", quarter if quarter != "None" else "Not specified")

if uploaded_file:
    st.write(f"Processing file: {uploaded_file.name}")

    # Save the uploaded file to disk to be able to read it with PyPDF2
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Find sections and Thuyet Minh part
    sections = find_table(uploaded_file.name)

    # Display section info
    st.write("**Section Information:**")
    for section, (start, end) in sections.items():
        st.write(f"{section}: Pages {start} to {end}")

        