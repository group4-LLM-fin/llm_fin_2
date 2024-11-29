import streamlit as st
st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)
st.title('Welcome!!!')
st.image('graphics/anya_logo.png', width=200)
st.header('Chat')
st.image("graphics/chat.png")
st.markdown("""
- Begin by typing your question or topic in the chatbox below.
- Our chatbot can help answer your queries, provide guidance in financial statements.
- Simply type a message and click **Send**. The chatbot will respond with helpful insights and suggestions.
""")

st.header('Data')
st.image("graphics/data.png")
st.markdown("""
On this page, you can view the financial statements you've uploaded and explore key information
- After uploading your financial statement file, the data will be displayed in a structured table.
- The table will contain important details about the financial statements, including:
  - **Year**: The year of the financial data.
  - **Quarter**: The relevant quarter of the year (e.g., Q1, Q2, etc.).
  - **Bank Name**: The name of the bank or financial institution associated with the statement.
""")
st.header('Upload')
st.image("graphics/upload.png")
st.markdown("""
The Upload page allows you to upload your financial statement file, and the system will automatically process and display the key financial tables: **Balance Sheet**, **Income Statement**, and **Cash Flow**. Here's what you need to do:

---

#### **Step 1: Upload Your Financial Statement File**
- To begin, click the **Upload file** in the **Upload** tab.

#### **Step 2: Wait for the Upload and Processing**
- Once your file is uploaded, the system will process it and generate the financial tables.
- The process usually takes **1 to 2 minutes** depending on the file size and data complexity.
- During this time, the system will extract the relevant financial information from your file and organize it into the following sections:

  - **Balance Sheet**: Displays the company’s assets, liabilities, and equity at a specific point in time.
  - **Income Statement**: Shows the company's revenue, expenses, and profits over a given period (e.g., quarterly or yearly).
  - **Cash Flow**: Provides an overview of the company’s cash inflows and outflows, broken down into operating, investing, and financing activities.

---

#### **Step 3: View the Financial Tables**
- After the processing is complete, you will be able to view the following financial tables:
  - **Balance Sheet**: A table displaying key metrics such as total assets, liabilities, and equity.
  - **Income Statement**: A table showing revenue, gross profit, operating income, and net profit.
  - **Cash Flow Statement**: A table that details the cash flows from operating, investing, and financing activities.
- **View Detailed Tables**: Each table can be expanded for more detailed data inspection.
---

#### **Step 5: Need Help?**
- If you experience any issues with the upload or processing, feel free to contact our support team at **maphquochung@gmail.com**.
- For assistance with interpreting the financial statements, our chatbot is available for quick guidance.

---
""")