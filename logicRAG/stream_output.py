from utils.ModelAPI import getStreamResponse
from dotenv import load_dotenv
from utils.MessageGeminiFormat import transform_response_for_gemini

load_dotenv()

def responseGenerate(memory_variables, model = 'gemini-1.5-flash'):
    # Append the new user message to the chat history
    history = memory_variables.get("chat_history", [])
    response = getStreamResponse(model=model, history=history)
    
    if 'gpt' in model:
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            yield str(chunk_message) if chunk_message else ""

    elif 'gemini' in model:
        for chunk in response:
            yield chunk.text

        history = transform_response_for_gemini(history)

    return history