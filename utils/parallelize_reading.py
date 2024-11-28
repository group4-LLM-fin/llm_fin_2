from OCR.readReport import *
from openai import OpenAI
from typing import List

def process_balancesheet(images, balancesheetPage, model, metadata):
    balancesheet = dict()
    for i in range(balancesheetPage[0], balancesheetPage[1] + 1):
        balancesheetPageInfo = readBalanceSheet(image=images[i], model=model, metadata=metadata)
        balancesheet.update(balancesheetPageInfo)
    return balancesheet

def process_incomestatement(images, isPage, model, metadata):
    incomestatement = dict()
    for i in range(isPage[0], isPage[1] + 1):
        isPageInfo = readIncome(image=images[i], model=model, metadata=metadata)
        incomestatement.update(isPageInfo)
    return incomestatement

def process_cashflow(images, cfPage, model, metadata):
    cashflow = dict()
    for i in range(cfPage[0], cfPage[1] + 1):
        cfPageInfo = readCashFlow(image=images[i], model=model, metadata=metadata)
        cashflow.update(cfPageInfo)
    return cashflow

def process_explanation(texts:List, model: OpenAI):
    response = model.embeddings.create(
    input=texts,
    model="text-embedding-3-large"
    )

    embeddings = []

    for doc in response.data:
        embeddings.append(doc.embedding)

    return embeddings
