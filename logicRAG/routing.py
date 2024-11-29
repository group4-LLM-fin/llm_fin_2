import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from utils.ModelAPI import getResponse
from logicRAG.ques2sql import Quest2SQL
from database.vectorDB import VectorDB

def sqlDecide(history:dict, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini'):
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
            If the user ask to find Vietnam Bank financial data or any related data that may have in bank financial report, but not relate to these 3 tables, like general information of the bank, the AI say "Retrieve".
            Else the AI say "No".
            The AI only response "SQL", "Retreive" or "No" and do not say anything further.
        '''
    }]
    
    _history = []
    _history.extend(history['chat_history'])
    _history.extend(prompt)
    completion = getResponse(llm=llm, history=_history, model=model)
    response = completion.choices[0].message.content

    return response.lower().replace(".", "")

def query_RAG(history, reports, vectordb: VectorDB, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini'):
    prompt = [{
        'role':'system',
        'content': '''
            This is the chat history of the user and AI. Now, the task of AI is to refine the question and convert it to format for a retrieval task. 
            Return the refined question in the language that user use.
            For example:
            User: "Ngân hàng ACB có bao nhiêu công ty con?"
            AI: "Ngân hàng ACB bao gồm các công ty con"
        '''
    }]
    _history = []
    _history.extend(history['chat_history'])
    _history.extend(prompt)
    completion = getResponse(llm=llm, history=_history, model=model)
    response = completion.choices[0].message.content

    prompt_report = [{
        'role':'system',
        'content': f'''
            Now, the task of AI is to define which report the user want to retreive from. 
            Here are the finacial report available: {reports}. The reportid contain bank name - years - quarter (eg. vcb-2024-2)
            If the user ask general information of a bank, return the newest report of that bank.
            The AI must thinking itself which bank and which report user want to choose to retrieve from.
            Only return the report id (eg. vcb-2024-2), do not say anything further.
            For example:
            User: "VPB có bao nhiêu công ty con?"
            AI: "vpb-2024-1"
        '''
    }]
    _history_report = []
    _history_report.extend(history['chat_history'])
    _history_report.extend(prompt_report)
    completion_report = getResponse(llm=llm, history=_history_report, model=model)
    response_report = completion_report.choices[0].message.content
    results = vectordb.query_with_distance_rag(
        response, 
        table_name="chunkEmbedding",
        distance='L2',
        columns=["text"], 
        where_clauses=[
        f"reportid = '{response_report}'"
        ],
        limit=3
    )

    result = " ".join(item['text'] for item in results[0])
    return result

def retransform_question(history, llm: OpenAI|genai.GenerativeModel, model='gpt-4o-mini'):
    prompt = [{
        'role':'system',
        'content': '''
            This is the chat history of the user and AI. Now, the task of AI is to summarize and return the final question that user want to ask. 
            Return the refined question in the english.
            For example:
            User: "ROE của VCB quý 2 2023 là bao nhiêu?"
            AI: "What is the ROE of VCB in quarter 2 year 2023?"
        '''
    }]
    _history = []
    _history.extend(history['chat_history'])
    _history.extend(prompt)
    completion = getResponse(llm=llm, history=_history, model=model)
    response = completion.choices[0].message.content
    return response

def routing(sql_engine, db_structure, reports, acc_name, vectordb: VectorDB, history:dict, llm:OpenAI|genai.GenerativeModel, model = 'gpt-4o-mini', ):
    decision = sqlDecide(history, llm, model = model)
    if  'sql' in decision :
        with st.spinner('Thinking...'):
            reformatted_ques = retransform_question(history,llm)
            text2sql_instance = Quest2SQL(model="gpt-4o", engine=sql_engine, db_structure=db_structure, acc_name=acc_name, db=vectordb)
            query_res, sql_queries = text2sql_instance.get_result(reformatted_ques)
            print(query_res, sql_queries)
        return query_res, sql_queries
    
    elif 'retrieve' in decision:
        with st.spinner('Thinking...'):
            query_RAG_res = query_RAG(history=history, reports = reports, vectordb=vectordb, llm=llm, model=model)
        return query_RAG_res, None

    else:
        return None, None