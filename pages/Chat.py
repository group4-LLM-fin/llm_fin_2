import streamlit as st
from RAG_logic.stream_output import get_gpt_response

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# Display previous chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box for user to chat with the bot
input_text = st.chat_input("Chat with your bot here")

# Stream the response and update the UI
def stream_response(response_generator):
    assistant_message = st.chat_message("ai").empty()  # Placeholder for assistant response
    streamed_text = ""  # To accumulate the streamed tokens

    # Stream each token and update the placeholder
    for chunk in response_generator:   
        streamed_text += chunk  # Append each token chunk
        assistant_message.write(streamed_text)  # Update the message in real-time
    
    return streamed_text


# When the user inputs a message
if input_text:
    # Show user's message immediately
    with st.chat_message("user"):
        st.markdown(input_text)

    # Append user's message to the chat history
    st.session_state.chat_history.append({"role": "user", "content": input_text})

    # Call the GPT API with streaming
    with st.spinner("Thinking..."):
        # Get the generator for the streaming response
        response_generator = get_gpt_response(st.session_state.chat_history, input_text)

        # Stream the response and display it
        chat_response = stream_response(response_generator)

    # Append assistant's response to the chat history
    st.session_state.chat_history.append({"role": "assistant", "content": chat_response})
