from database.baseDatabase import Database
from database.vectorDB import VectorDB
import os
from dotenv import load_dotenv
import uuid
import concurrent.futures

def insert_metadata(metadata, db: Database):
    db.insert("METADATA", **metadata)

def insert_balancesheet(metadata, response_llm: str|dict, vectordb: VectorDB, db: Database):
  
    # Mapping account name
    if response_llm is str:
        bs = json.loads(response_llm)
    else:
        bs = response_llm

    reportid = [metadata['reportid']]*len(bs)
    accno, accname, amount = [], [], []
    query_texts = list(bs.keys())
    
    # Mapping account no.
    results = vectordb.query_with_distance(
        query_texts, 
        table_name="ACCNO",
        distance='L2',
        columns=["accno", "accname"], 
        where_clauses=[
        "report = 'BS'"
        ],
        limit=1
    )
    
    for i,key in zip(range(len(results)),query_texts):
        accno.append(results[i][0]['accno'])
        accname.append(results[i][0]['accname'])
        amount.append(bs[key])

    # Commit data
    records = [
    (str(uuid.uuid4()), reportid[i], accno[i], accname[i], amount[i])
    for i in range(len(accno))
    ]

    sql = """
    INSERT INTO "BALANCESHEET" (id, reportid, accountno, accountname, amount)
    VALUES (%s, %s, %s, %s, %s);
    """
    
    db.execute_many(query=sql, records=records)

def insert_income(metadata, response_llm: str|dict, vectordb: VectorDB, db: Database =None):
    # Mapping account name
    if response_llm is str:
        bs = json.loads(response_llm)
    else:
        bs = response_llm

    reportid = [metadata['reportid']]*len(bs)
    accno, accname, amount = [], [], []
    query_texts = list(bs.keys())
    
    # Mapping account no.
    results = vectordb.query_with_distance(
        query_texts, 
        table_name="ACCNO",
        distance='L2',
        columns=["accno", "accname"], 
        where_clauses=[
        "report = 'IS'"
        ],
        limit=1
    )
    for i,key in zip(range(len(results)),query_texts):
        accno.append(results[i][0]['accno'])
        accname.append(results[i][0]['accname'])
        amount.append(bs[key])

    # Commit data
    records = [
    (str(uuid.uuid4()), reportid[i], accno[i], accname[i], amount[i])
    for i in range(len(accno))
    ]

    sql = """
    INSERT INTO "INCOMESTATEMENT" (id, reportid, accountno, accountname, amount)
    VALUES (%s, %s, %s, %s, %s);
    """
    
    db.execute_many(query=sql, records=records)

def insert_cashflow(metadata, response_llm: str|dict, vectordb: VectorDB, db: Database =None):
    if response_llm is str:
        bs = json.loads(response_llm)
    else:
        bs = response_llm

    reportid = [metadata['reportid']]*len(bs)
    accname, amount = [], []
    query_texts = list(bs.keys())
    
    # Mapping account no.
    results = vectordb.query_with_distance(
        query_texts, 
        table_name="ACCNO",
        distance='L2',
        columns=["accname"], 
        where_clauses=[
        "report = 'CS'"
        ],
        limit=1
    )
    for i,key in zip(range(len(results)),query_texts):
        accname.append(results[i][0]['accname'])
        amount.append(bs[key])

    # Commit data
    records = [
    (str(uuid.uuid4()), reportid[i], accname[i], amount[i])
    for i in range(len(amount))
    ]

    sql = """
    INSERT INTO "CASHFLOW" (id, reportid, accountname, amount)
    VALUES (%s, %s, %s, %s);
    """
    
    db.execute_many(query=sql, records=records)

def insert_chunk():
    pass

def insert_all(metadata, bs: str|dict, ics: str|dict, cf: str|dict , vectordb: VectorDB, db: Database):
    insert_metadata(metadata, db)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        balancesheet_future = executor.submit(insert_balancesheet, metadata, bs, vectordb, db)
        income_future = executor.submit(insert_income, metadata, ics, vectordb, db)
        cashflow_future = executor.submit(insert_cashflow, metadata, cf, vectordb, db)
        
        balancesheet_future.result() 
        income_future.result()
        cashflow_future.result()


if __name__ == '__main__':
    metadata = {
        'reportid': 'vcb-2021-3',
        'bankid': 1203001,
        'year': 2021,
        'quarter': 3,
        'banksymbol': 'VCB'
    }

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

    vectordb = VectorDB(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )