from openai import OpenAI
import google.generativeai as genai
from utils.ModelAPI import getResponse
from logicRAG.ques2sql import Quest2SQL

def sqlDecide(history:dict, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini'):
    input = history['chat_history'][-1]
    prompt = [{
        'role':'system',
        'content': '''
            This is the question of the user. The task of AI decide to start a SQL query search about financial data or not. 
            If the user ask anything that require to find Vietnam Bank financial data then the AI say Yes. 
            The AI only response Yes or No and do not say anything further.
        '''
    }]
    
    if input['role'] == 'user':
        prompt.append(input)
        completion = getResponse(llm=llm, history=prompt, model=model)
        response = completion.choices[0].message.content
    return response.lower().replace(".", "")

def routing(sql_engine, db_structure, acc_name, history:dict, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini', ):
    decision = sqlDecide(history, llm, model = model)
    
    if 'yes' in decision:
        text2sql_instance = Quest2SQL(model="gpt-4o", engine=sql_engine, db_structure=db_structure, acc_name=acc_name)
        query_res = text2sql_instance.get_result(history['chat_history'][-1]['content'])
        print(query_res)