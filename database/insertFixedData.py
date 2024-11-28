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
    
    report = []
    accountName = []
    accountNo = []
    for key, value in data.items():
        accountName.append(value)
        accountNo.append(key)
        acc = str(key)
        if acc[0] in ['1','2','3','4','5','6']:
            report.append("BS")
        elif acc[0] in ['7','8']:
            report.append("IS")

    accEmbed = get_embedding_voyage(texts=accountName, client=embedder)
    print(f'Get {len(accEmbed), len(report)} embeddings successfuly')
    
    records = [
    (str(uuid.uuid4()), accountNo[i], accountName[i], accEmbed[i], report[i])
    for i in range(len(accountNo))
    ]

    sql = """
    INSERT INTO "ACCNO" (id, accno, accname, embedding, report)
    VALUES (%s, %s, %s, %s, %s);
    """
    db.execute_many(query=sql, records=records)

def insertCashflow(db: Database = None, embedder = None):
    sections = [
    "Cash Flows from Operating Activities",
    "Interest income and similar earnings received",
    "Interest expenses and similar expenses paid",
    "Net income from services received",
    "Foreign exchange, gold, and securities trading gains/losses",
    "Other expenses paid",
    "Cash for other handled and risk-provisioned accounts",
    "Cash paid to employees in management activities",
    "Corporate income tax paid in the year",
    "Net cash flow from operating activities before changes in assets and liabilities",
    "Increase/Decrease in Operating Assets",
    "Deposits to other credit institutions",
    "Investment in securities",
    "Loans to customers and finance leases",
    "Customer deposits",
    "Provision for loan losses",
    "Other operating assets"
    "Increase/Decrease in Liabilities",
    "Deposits from the State Bank of Vietnam",
    "Deposits from other credit institutions",
    "Deposits from customers",
    "Grants and investments received",
    "Payables and accrued expenses",
    "Net Cash Flow from (used in) Operating Activities",
    "Cash Flows from Investing Activities",
    "Purchase of fixed assets",
    "Proceeds from disposal of fixed assets",
    "Payments for acquisitions, disposals of other investments",
    "Capital contribution to other entities",
    "Proceeds from capital contributions to other entities",
    "Dividends and profits received from investments",
    "Net cash flow from investing activities",
    "Cash Flows from Financing Activities",
    "Dividends paid to shareholders",
    "Net cash flow from financing activities",
    "Net cash flow for the year",
    "Cash and cash equivalents at the beginning of the year",
    "Cash and cash equivalents at the end of the year"
    ]

    accEmbed = get_embedding_voyage(texts=sections, client=embedder)
    report = ["CS"]*len(sections)

    records = [
    (str(uuid.uuid4()), sections[i], accEmbed[i], report[i])
    for i in range(len(sections))
    ]

    sql = """
    INSERT INTO "ACCNO" (id, accname, embedding, report)
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
    insertCashflow(db=db, embedder=vo)
    

