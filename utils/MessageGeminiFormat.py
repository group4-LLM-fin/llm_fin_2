def transform_history_for_gemini(history):
    transformed_history = list(history)
    for message in history:
        message["parts"] = message.pop("content")
        if message['role'] == 'assistant':
            message['role'] = 'model'   
    message = transformed_history.pop(-1)
    return transformed_history, message['parts']

def transform_response_for_gemini(history):
    for message in history:
        message["content"] = message.pop("parts") 
        if message['role'] == 'model':
            message['role'] = 'assistant'
    return history
