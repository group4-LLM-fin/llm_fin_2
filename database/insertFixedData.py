import pandas as pd
import voyageai.client
from baseDatabase import Database
from dotenv import load_dotenv
import os
from vectorDB import VectorDB
import json
import uuid
from openai import OpenAI
import voyageai
import numpy as np

def get_embedding_voyage(texts, client: voyageai.Client):
    
    embeddings = client.embed(texts, model="voyage-finance-2", input_type="document")
    embeddings = embeddings.embeddings

    return embeddings

def get_embedding(texts, model="text-embedding-3-small", client: OpenAI = None):
   texts =[text.replace("\n", " ") for text in texts]
   return client.embeddings.create(input = texts, model=model).data

def insertBankData(db: Database):
    bankName = pd.read_excel('data/bank_data.xlsx')
    bank_data = [
        (row['Bank Code'], row['Bank Name'], row['Abbreviation'], row['Symbol'])  # or modify as needed
        for index, row in bankName.iterrows()
    ]
    for code, name, abbr, symbol in bank_data:
        db.insert('BANK', bankid=code, bankname=name, abbreviation=abbr, symbol=symbol)

def insertAccountData(db: Database = None, embedder = None):
    with open('data/tk_eng.json','r', encoding='utf-8') as f:
        data = json.load(f)

    accountName = []
    accountNo = []
    for key, value in data.items():
        accountName.append(value)
        accountNo.append(key)

    accEmbed = get_embedding_voyage(texts=accountName, client=embedder)
    print(f'Get {len(accEmbed)} embeddings successfuly')
    
    records = [
    (str(uuid.uuid4()), accountNo[i], accountName[i], accEmbed[i])
    for i in range(len(accountNo))
    ]

    sql = """
    INSERT INTO "ACCNO" (id, accno, accname, embedding)
    VALUES (%s, %s, %s, %s);
    """
    db.execute_many(query=sql, records=records)
        

if __name__ == '__main__':
    load_dotenv()

    user = os.getenv('USER')
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DB1')
    voyage_api = os.getenv('VOYAGE_API')

    # Initialize database connection
    db = Database(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

    vo = voyageai.Client(api_key=voyage_api)

    
    # insertBankData(db=db)

    vectorDB = VectorDB(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

    insertAccountData(db = db, embedder=vo)
    

