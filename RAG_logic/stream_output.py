import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_gpt_response(history, prompt):
    # Append the new user message to the chat history
    history.append({"role": "user", "content": prompt})

    # Send the chat history to OpenAI's API and stream the response
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  
        messages=history,
        stream=True
    )

    full_response = ""
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta'].get('content', '')
        full_response += chunk_message
        yield chunk_message

    # Append the assistant's response to the chat history
    history.append({"role": "assistant", "content": full_response})

    return history
