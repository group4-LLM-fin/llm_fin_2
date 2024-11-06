import numpy as np
from PIL import Image
import pytesseract
from unidecode import unidecode
import pandas as pd
import json
import google.generativeai as genai
import streamlit as st


def find_table(images):

    signals = {
        1: ('balance sheet', ['tien mat', 'vang', 'da quy']),
        2: ('income statement', ['thu nhap lai thuan', 'lai thuan','chi phi hoat dong', 'chi phi', 'tong loi nhuan']),
        3: ('cash flow', ['luu chuyen tien']),
        4: ('thuyet minh', ['don vi bao cao', 'dac diem hoat dong', 'thanh lap va hoat dong']),
    }
    metadata = ""
    result = [np.nan] * len(images)
    k = 1
    progress_bar = st.progress(0, text='Optical Character Recognizing...')
    for i, image in enumerate(images): 

        text = pytesseract.image_to_string(image, lang='vie')  # Pass PIL image to pytesseract
        test_text = unidecode(text.lower())
        
        if i < 3:
            metadata += text
            metadata += " "

        if k in signals:
            label, current_signals = signals[k]
            if any(signal in test_text for signal in current_signals):
                result[i] = k
                k += 1
            else:
                result[i] = result[i-1] if i > 0 else np.nan
        else:
            result[i] = result[i-1] if i > 0 else np.nan
        if k == 5:
            for j in range(i+1,len(result)):
                result[j] = 4
            break
        progress_bar.progress(i+1, 'Optical Character Recognizing...')
        
        # if result[i] == 4:
        #     first_half, second_half = split_text_by_sentences(text)
        #     embedding1 = embedder.embed_documents(texts=first_half)
        #     embedding1 = embedding1[0]
        #     embedding2 = embedder.embed_documents(texts=second_half)
        #     embedding2 = embedding2[0]
        #     db.insert_embedding(
        #         table_name="EXPLANATION",
        #         bank = bank,
        #         year = year,
        #         quarter = quarter, 
        #         text = first_half, 
        #         page = i, 
        #         part = 1, 
        #         Embedding = embedding1
        #     )
        #     db.insert_embedding(
        #         table_name="EXPLANATION",
        #         bank = bank,
        #         year = year,
        #         quarter = quarter, 
        #         text = second_half, 
        #         page = i, 
        #         part = 2, 
        #         Embedding = embedding2
        #     )
    progress_bar.empty()
    result_filled = pd.Series(result).map({1: 'balance sheet', 2: 'income statement', 3: 'cash flow', 4: 'thuyet minh'}).fillna('muc luc').tolist()

    # Logging each section range for display
    sections = {
        "Catalouge": (0, result_filled.index('balance sheet') - 1),
        "Balance Sheet": (result_filled.index('balance sheet'), result_filled.index('income statement') - 1),
        "Income Statement": (result_filled.index('income statement'), result_filled.index('cash flow') - 1),
        "Cash Flow Statement": (result_filled.index('cash flow'), result_filled.index('thuyet minh') - 1),
        "Explanation": (result_filled.index('thuyet minh'), len(result_filled) - 1)
    }

    return sections, metadata

def split_text_by_sentences(text):
    sentences = text.split('. ')
    midpoint = len(sentences) // 2
    first_half = '. '.join(sentences[:midpoint]) + '.'
    second_half = '. '.join(sentences[midpoint:])
    return first_half, second_half

def get_metadata(extracted_text, model:genai.GenerativeModel):

    response = model.generate_content(["""
        Đây là báo cáo tài chính của ngân hàng nào:
        Các ngân hàng có trong database là:
        [('Ngân hàng TM TNHH MTV Dầu khí Toàn Cầu', 79320001), ('Ngân hàng TMCP Bản Việt', 79327001), ('Ngân hàng TMCP Đông Nam Á', 1317001), ('Ngân hàng TMCP Nam Á', 79306001), ('Ngân hàng TMCP Phát triển Thành phố Hồ Chí Minh', 79321001), ('Ngân hàng TMCP Phương Đông', 79333001), ('Ngân hàng TMCP Quốc tế Việt Nam', 79314013), ('Ngân hàng TMCP Sài Gòn Hà Nội', 1348002), ('Ngân hàng TMCP Sài Gòn', 79334001), ('Ngân hàng TMCP Việt Á', 1355002), ('Ngân hàng TNHH MTV ANZ Việt Nam', 79602001), ('Ngân hàng TNHH MTV CIMB Việt Nam', 1661001), ('Ngân hàng TNHH MTV Standard Chartered Việt Nam', 1604001), ('Ngân hàng TMCP Tiên Phong', 1358001), ('Ngân hàng TMCP Bảo Việt', 1359001), ('Ngân hàng TNHH MTV Shinhan Việt Nam', 79616001), ('Ngân hàng TNHH Indovina', 79502001), ('Ngân hàng TMCP Quốc Dân', 1352002), ('Ngân hàng TNHH MTV Woori Việt Nam', 1663001), ('Ngân hàng TMCP Thịnh Vượng và Phát Triển', 1341001), ('Ngân hàng Citibank', 79654001), ('NH TMCP Á Châu', 79307001), ('NHTMCP An Bình', 1323002), ('NH TMCP Quân Đội', 1311001), ('NHTMCP Hàng Hải', 1302001), ('NH Việt Nam Thịnh Vượng', 1309001), ('NHTMCP Ngoại Thương Việt Nam', 1203001), ('NH Nông nghiệp và Phát triển Nông thôn Việt Nam', 1204009), ('NHTMCP Kỹ Thương Việt Nam', 1310001), ('NH TMCP Công thương Việt Nam', 1201001), ('NHTMCP Sài Gòn Thương Tín', 79303001), ('NH TMCP Đầu Tư và Phát triển Việt Nam', 1202001), ('NH TMCP Xuất Nhập Khẩu', 79305001), ('NH Hong Leong Việt Nam', 79603001), ('NH TMCP Kiên Long', 79353001), ('Ngân hàng TMCP Lộc Phát Việt Nam', 1357001), ('NH TM TNHH MTV Đại Dương', 1319001), ('NH TNHH MTV Public Việt Nam', 1501001), ('NH Deutsche Bank', 79619001), ('NH TMCP Sài Gòn Công Thương', 79308001)]
        Chỉ trả về dạng Json, ngoài ra không giải thích gì thêm, theo format ví dụ:
            {"banksymbol": "VCB",
            "year": 2024,
            "quarter": 3,
            "reportid": "vcb-2024-3",
            "bankid": 01203001}
        Thông tin ngân hàng cần phân tích:
        """ + extracted_text])
    
    metadata = response.text.replace("json","")
    metadata = metadata.replace("```","")
    metadata = json.loads(metadata)

    return metadata