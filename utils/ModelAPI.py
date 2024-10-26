import openai
import google.generativeai as genai
from dotenv import load_dotenv
import os
from utils.MessageGeminiFormat import transform_history_for_gemini

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def getStreamResponse(model = "gpt-4o-mini", history = None):

    if history is None:
        history = []

    if 'gpt' in model:
        response = openai.ChatCompletion.create(
            model=model,  
            messages=history,
            stream=True
        )

    if 'gemini' in model:
        history, message = transform_history_for_gemini(history)
        model = genai.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat(history=history)
        response = chat.send_message(
            content = message,
            stream = True
        )

    return response