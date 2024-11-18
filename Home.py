import streamlit as st
st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)
st.title('Welcome')

import os
os.system("sudo mkdir -p /usr/share/tesseract-ocr/4.00/tessdata")
os.system("sudo cp ./tessdata/vie.traineddata /usr/share/tesseract-ocr/4.00/tessdata/")
os.system("sudo chmod 644 /usr/share/tesseract-ocr/4.00/tessdata/vie.traineddata")

# Check if the directory exists
print("Checking tessdata directory contents:")
os.system("ls -la /usr/share/tesseract-ocr/4.00/tessdata")

# Check if the file exists in the working directory
print("Checking local tessdata directory contents:")
os.system("ls -la ./tessdata")
