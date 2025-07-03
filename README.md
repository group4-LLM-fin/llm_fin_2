# Anya Financial Expert
<p align="center">
  <img src="graphics/anya_logo.png" alt="Logo" width="80">
</p>

This app is an implementation of an end-to-end model for LLM finacial document understanding. In this project we focus on analysis from bank financial documents.
![Architecture Diagram](llm_structure.png)
# Project Structure

```plaintext
.
├── .env.example
├── .gitignore
├── Dockerfile
├── Home.py
├── packages.txt
├── README.md
├── requirements.txt
├── test.Json
├── .streamlit/
│   └── config.toml
├── database/
│   ├── baseDatabase.py
│   ├── insertFixedData.py
│   ├── setUpDatabase.py
│   └── vectorDB.py
├── graphics/
│   ├── ...
├── logicRAG/
│   ├── ques2sql.py
│   ├── routing.py
│   └── stream_output.py
├── OCR/
│   ├── analyzeReport.py
│   ├── insertData.py
│   ├── readReport.py
│   └── __init__.py
├── pages/
│   ├── Chat.py
│   ├── Data.py
│   ├── Upload.py
│   └── __init__.py
├── resource/
│   ├── example.txt
│   ├── explanation_part.txt
│   └── RAG_get_anwser.py
└── utils/
    ├── getEmbedding.py
    ├── latex.py
    ├── MessageGeminiFormat.py
    ├── ModelAPI.py
    ├── parallelize_reading.py
    └── __init__.py

```
# Getting started

### Prerequisites

Before you can run this app, make sure you have the following prerequisites installed:

- Python 3.9 or higher
- API Key for: OPENAI, GOOGLE-GENAI, VOYAGEAI
- Database
- Pip (Python package manager)
- Other required Python packages (see the [Installation](#installation) section)

### Clone the Repository

To get started, clone this repository to your local machine using the following command:

```cmd
git clone https://github.com/group4-LLM-fin/llm_fin_2.git
cd llm_fin_2
```
### Installation
Create and activate a virtual environment (optional but recommended)
```cmd
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
Install dependencies
```cmd
pip install -r requirements.txt
```

### Add env variable
- Create .env file in root of project
- Add environment variable like in .env.example file

### Start the app
```cmd
streamlit run Home.py --server.port 6789
```

# TO DO
- [x] Project Structure
  - [x]  Complete project structure: create environment, adding requirements.txt and .env files
  - [x]  Deployment
  - [x]  Database setting
- [ ] Implement RAG logic
  - [x] LLM API
  - [x] Embedding search
  - [x] Text to SQL
  - [x] Chain of thought
  - [x] SQL query
  - [ ] Fix SQL  query in case error
  - [x] Evaluation
- [ ] Implement OCR
  - [x] Pytesseract
  - [x] Vision Language model
  - [x] Analyze documment
  - [x] Evaluation
  
