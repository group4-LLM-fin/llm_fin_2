import streamlit as st
from langchain.memory import ConversationBufferMemory
from logicRAG.stream_output import responseGenerate

st.set_page_config(
    page_title="Chatbot",
    page_icon="graphics/anya_logo.png" 
)
st.logo('graphics/logo.png')

with st.chat_message(avatar="graphics/ico.jpg", name="system"):
    st.markdown("© 2024 Grp4ML1 - DSEB64A. All rights reserved.")

if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

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

    # Stream each token and update the placeholder
    for chunk in response_generator:   
        streamed_text += chunk 
        assistant_message.write(streamed_text)  # Update the message in real-time
    
    return streamed_text

# When the user inputs a message
if input_text:
    with st.chat_message("user", avatar='graphics/loid.png'):
        st.markdown(input_text)

    st.session_state.memory.chat_memory.add_message({"role": "user", "content": input_text})

    response_generator = responseGenerate(st.session_state.memory.load_memory_variables({}), model = 'gpt-4o-mini')

    chat_response = streamResponse(response_generator)

    st.session_state.memory.chat_memory.add_message({"role": "assistant", "content": chat_response})
