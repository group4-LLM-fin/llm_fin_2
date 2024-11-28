import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from utils.ModelAPI import getResponse
from logicRAG.ques2sql import Quest2SQL
from database.vectorDB import VectorDB

def sqlDecide(history:dict, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini'):
    input = history['chat_history'][-1]
    # except:
    #     try:
    #         input = history['chat_history'][-3:]
    #     except:
    #         try:
    #             input = history['chat_history'][-1:]
    #         except Exception as e:
    #             print("Error reading history:", e)

    prompt = [{
        'role':'system',
        'content': '''
            This is the question of the user. The task of AI decide to start a SQL query search about financial data or not. 
            If the user ask anything that require to find Vietnam Bank financial data relate to 3 tables: Income statement, balance sheet, Cashflow statement then the AI say "SQL".
            If the user ask to find Vietnam Bank financial data or any related data that may have in bank financial report, but not relate to these 3 tables the AI say "Retrieve".
            Else the AI say "No".
            The AI only response "SQL", "Retreive" or "No" and do not say anything further.
        '''
    }]
    
    if input['role'] == 'user':
        prompt.append(input)
        completion = getResponse(llm=llm, history=prompt, model=model)
        response = completion.choices[0].message.content
    return response.lower().replace(".", "")

def query_RAG(history:dict,vectordb: VectorDB, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini'):
    input = history['chat_history'][-1]
    prompt = [{
        'role':'system',
        'content': '''
            This is the question of the user. The task of AI is to refine the question and convert it to format for a retrieval task. 
            Return the refined question in the language that user use.
            For example:
            User: "Ngân hàng ACB có bao nhiêu công ty con?"
            AI: "Ngân hàng ACB bao gồm các công ty con"
        '''
    }]
    
    if input['role'] == 'user':
        prompt.append(input)
        completion = getResponse(llm=llm, history=prompt, model=model)
        response = completion.choices[0].message.content

    results = vectordb.query_with_distance_rag(
        response, 
        table_name="chunkEmbedding",
        distance='L2',
        columns=["text"], 
        where_clauses=[
        "reportid = 'acb-2024-1'"
        ],
        limit=3
    )

    result = " ".join(item['text'] for item in results[0])
    return result

def routing(sql_engine, db_structure, acc_name, vectordb: VectorDB, history:dict, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini', ):
    decision = sqlDecide(history, llm, model = model)
    print(decision)
    if  'sql' in decision :
        with st.spinner('Thinking...'):
            text2sql_instance = Quest2SQL(model="gpt-4o", engine=sql_engine, db_structure=db_structure, acc_name=acc_name)
            query_res, sql_queries = text2sql_instance.get_result(history['chat_history'][-1]['content'])
            print(query_res, sql_queries[0])
        return query_res, sql_queries
    
    elif 'retrieve' in decision:
        with st.spinner('Thinking...'):
            query_RAG_res = query_RAG(history=history,vectordb=vectordb, llm=llm, model=model)
            print(query_RAG_res)
        return query_RAG_res, None

    else:
        return None, None