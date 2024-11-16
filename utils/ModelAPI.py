from utils.MessageGeminiFormat import transform_history_for_gemini
from openai import OpenAI
import google.generativeai as genai

def getStreamResponse(llm:OpenAI|genai.GenerativeModel, model = "gpt-4o-mini", history = None):

    if history is None:
        history = []

    if 'gpt' in model:
        response = llm.chat.completions.create(
            model=model,  
            messages=history,
            stream=True
        )

    if 'gemini' in model:
        history, message = transform_history_for_gemini(history)
        chat = llm.start_chat(history=history)
        response = chat.send_message(
            content = message,
            stream = True
        )

    return response