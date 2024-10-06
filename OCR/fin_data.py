"""
This is not OCR implementation yet. This part of code is only a demo that using provided data.
The OCR implementation will be added later.
"""

from vnstock3 import Vnstock
import pandas as pd

def get_fin_data(): 
    stock = Vnstock().stock(symbol='TCB', source='VCI')
    df = stock.finance.income_statement(period='year', lang='vi').head()
    new_columns = []
    for i, col in enumerate(df.columns):
        if col in df.columns[:i]:
            count = df.columns[:i].tolist().count(col)
            new_columns.append(f"{col}_{count + 1}")
        else:
            new_columns.append(col)

    df.columns = new_columns

    return df   