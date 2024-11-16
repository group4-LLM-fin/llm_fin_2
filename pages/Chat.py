import os
import openai
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai
from logicRAG.routing import routing
from logicRAG.stream_output import responseGenerate
from langchain.memory import ConversationBufferMemory

load_dotenv(override=True)

st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)
st.logo('graphics/logo.png')

@st.cache_resource
def connectapi():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gpt = OpenAI()
    gemini = genai.GenerativeModel("gemini-1.5-flash")

    return gpt, gemini
gpt, gemini = connectapi()

with st.chat_message(avatar="graphics/ico.jpg", name="system"):
    st.markdown("© 2024 Grp4ML1 - DSEB64A. All rights reserved.")

if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
    st.session_state.memory.chat_memory.add_message({"role": "system", "content": "The name of AI is Anya. It assist with querying Vietnam banking financial data."})
    
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

    # Routing
    
    
    response_generator = responseGenerate(llm=gpt, memory_variables= st.session_state.memory.load_memory_variables({}), model = 'gpt-4o-mini')

    chat_response = streamResponse(response_generator)

    st.session_state.memory.chat_memory.add_message({"role": "assistant", "content": chat_response})
