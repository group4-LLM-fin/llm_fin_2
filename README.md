# llm_fin
This app is an implementation of an end-to-end model for LLM finacial document understanding. In this project we focus on analysis from bank financial documents.

# Getting started

### Prerequisites

Before you can run this app, make sure you have the following prerequisites installed:

- Python 3.8 or higher
- Pip (Python package manager)
- [Streamlit](https://streamlit.io/) (if not already installed, you can install it using `pip install streamlit`)
- Other required Python packages (see the [Installation](#installation) section)

### Clone the Repository

To get started, clone this repository to your local machine using the following command:

```cmd
git clone https://github.com/group4-LLM-fin/llm_fin.git
cd llm_fin
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

### Start the app
```cmd
streamlit run Home.py --server.port 6789
```

# TO DO
- [x] Format project structure
  - [ ] [Minh Anh] Complete project structure: create environment, adding requirements.txt and .env files 
- [ ] [Ngoc] Implement RAG logic
  - [ ] LLM API
  - [ ] Embedding search
  - [ ] Reranking model
  - [ ] ...  
- [ ] [Hoang Minh] Implement OCR
  - [ ] OCR model weight
  - [ ] ...
