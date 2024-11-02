from baseDatabase import Database
from dotenv import load_dotenv
import os
from vectorDB import VectorDB

'''
Table names:

- BANK: baseDB
- METADATA: baseDB
- BALANCESHEET: baseDB
- INCOMESTATEMENT: baseDB
- CASHFLOW: baseDB
- ACCNO: vectorDB
- CHUNK: vectorDB
'''

bank = {
    'bankid' : 'INT PRIMARY KEY',
    'bankFullName' : 'TEXT',
    'abbreviation': 'TEXT',
    'Symbol': 'TEXT'
}

accNo = {
    'Id': 'UUID PRIMARY KEY',
    'accNo': 'INT CHECK (accNo>=1 and accNo<=9999) UNIQUE',
    'accName': 'TEXT',
    'embedding': 'VECTOR(1536)'
}

metadata = {
    'reportid': 'TEXT PRIMARY KEY',
    'bankid': 'INT REFERENCES "BANK"("bankid")',
    'year': 'INT CHECK (year >= 1900 AND year <= 2100)',
    'quarter': 'INT CHECK (quarter BETWEEN 0 AND 4)'
}

balanceSheet = {
    'Id': 'INT PRIMARY KEY',
    'reportid': 'TEXT, FOREIGN KEY REFERENCES "METADATA"("reportid")',
    'accountNo': 'INT, FOREIGN KEY REFERENCES "ACCNO"("accno")',
    'accountName': 'TEXT',
    'amount': 'DECIMAL(15, 2)'
}

incomeStatement = {
    'Id': 'INT PRIMARY KEY',
    'reportid': 'TEXT, FOREIGN KEY REFERENCES "METADATA"("reportid")',
    'accountNo': 'INT, FOREIGN KEY REFERENCES "ACCNO"("accno")',
    'accountName': 'TEXT',
    'amount': 'DECIMAL(15, 2)'
}

cashFlow = {
    'Id': 'INT PRIMARY KEY',
    'reportid': 'TEXT, FOREIGN KEY REFERENCES "METADATA"("reportid")',
    'accountName': 'TEXT',
    'amount': 'DECIMAL(15, 2)'
}

chunk = {
    "Id": "UUID PRIMARY KEY",
    "reportid": 'TEXT NOT NULL, FOREIGN KEY REFERENCES "METADATA"("reportid")',  
    "text": "TEXT",
    "embedding": "VECTOR(1536)"  
}

if __name__ == '__main__':
    load_dotenv()

    user = os.getenv('USER')
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    password = os.getenv('PASSWORD')
    dbname = os.getenv('DB1')

    # Initialize database connection
    db = Database(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

    vectorDB = VectorDB(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

    # Create tables up to ERD
    db.create_table('BANK', columns=bank)
    db.create_table('METADATA', columns=metadata)
    vectorDB.create_table('ACCNO', columns = accNo)
    db.create_table('BALANCESHEET', columns=balanceSheet)
    db.create_table('INCOMESTATEMENT', columns=incomeStatement)
    db.create_table('CASHFLOW', columns=cashFlow)
    vectorDB.create_table('CHUNK', columns = chunk)

    # db.add_column('BANK','abbreviation TEXT')
    db.execute(
        """
        ALTER TABLE bank
        ALTER COLUMN symbol SET DATA TYPE TEXT;
        """
    )
