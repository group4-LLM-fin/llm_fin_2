import os
import openai
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.engine import URL
import google.generativeai as genai
from logicRAG.routing import routing
from database.vectorDB import VectorDB
from sqlalchemy import create_engine, inspect
from logicRAG.stream_output import responseGenerate
from langchain_community.utilities import SQLDatabase
from langchain.memory import ConversationBufferMemory

load_dotenv(override=True)

st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)
st.logo('graphics/logo.png')

@st.cache_resource
def initializing():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gpt = OpenAI()
    gemini = genai.GenerativeModel("gemini-1.5-flash")

    #  SQL connection
    user = os.getenv('USER')
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DB1')
    sqlalchemy_connection_url = URL.create(
    "postgresql+psycopg2",
    username=user,
    password=password,
    host=host,
    port=port,
    database=dbname,
    )
    db_config = {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'dbname': dbname
    }

    vectordb = VectorDB(**db_config)
    sql_engine = create_engine(sqlalchemy_connection_url)
    inspector = inspect(sql_engine)
    sql_database = SQLDatabase(engine=sql_engine)
    return gpt, gemini, inspector, sql_engine, sql_database, vectordb

@st.cache_data
def getDatabaseInfo():
    db_structure = {
    'tables': inspector.get_table_names(),
    }
    db_structure.update({
        table: {
            'columns': [{'name': column['name'], 'type': str(column['type'])} for column in inspector.get_columns(table)]
        } for table in db_structure['tables']
    })
    
    acc_name_query = """
        SELECT accname
        FROM "ACCNO"
        """
    acc_name = sql_database.run(acc_name_query)
    
    return db_structure, acc_name

gpt, gemini, inspector, sql_engine, sql_database, vectordb = initializing()
db_structure, acc_name = getDatabaseInfo()

with st.chat_message(avatar="graphics/ico.jpg", name="system"):
    st.markdown("© 2024 Grp4ML1 - DSEB64A. All rights reserved.")

if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
    st.session_state.memory.chat_memory.add_message({"role": "system", "content": "The name of AI is Anya. It assist with querying Vietnam banking financial data. If the system found out something, Anya will explain to user the result with context of finance."})
    
# Display previous chat history
for message in st.session_state.memory.chat_memory.messages:
    if message["role"] == "assistant":
        with st.chat_message(message["role"], avatar='graphics/graphic.png'):
            st.markdown(message["content"])

    if message["role"] == "user":
        with st.chat_message(message["role"], avatar='graphics/loid.png'):
            st.markdown(message["content"])

input_text = st.chat_input("Chat with your bot here")

# Stream the response and update the UI
def streamResponse(response_generator):
    assistant_message = st.chat_message("ai", avatar='graphics/graphic.png').empty()  
    streamed_text = "" 

    for chunk in response_generator:   
        streamed_text += chunk 
        assistant_message.write(streamed_text)
    
    return streamed_text

# When the user inputs a message
if input_text:
    with st.chat_message("user", avatar='graphics/loid.png'):
        st.markdown(input_text)

    st.session_state.memory.chat_memory.add_message({"role": "user", "content": input_text})
    query_res, sql_queries = routing(history = st.session_state.memory.load_memory_variables({}), 
                    llm=gpt, model='gpt-4o-mini',
                    vectordb= vectordb,
                    sql_engine=sql_engine, acc_name=acc_name,
                    db_structure=db_structure)
    
    if sql_queries:
        st.session_state.memory.chat_memory.add_message({"role": "system", "content": f"SQL queries: {sql_queries}, query result: {query_res}"})
    else:
        st.session_state.memory.chat_memory.add_message({"role": "system", "content": f"Query results: {query_res}"})

    response_generator = responseGenerate(llm=gpt, memory_variables= st.session_state.memory.load_memory_variables({}), model = 'gpt-4o-mini')

    chat_response = streamResponse(response_generator)

    st.session_state.memory.chat_memory.add_message({"role": "assistant", "content": chat_response})
