from OCR.readReport import *

def process_balancesheet(images, balancesheetPage, model, metadata):
    balancesheet = dict()
    for i in range(balancesheetPage[0], balancesheetPage[1] + 1):
        balancesheetPageInfo = readBalanceSheetGem(image=images[i], model=model, metadata=metadata)
        balancesheet.update(balancesheetPageInfo)
    return balancesheet

def process_incomestatement(images, isPage, model, metadata):
    incomestatement = dict()
    for i in range(isPage[0], isPage[1] + 1):
        isPageInfo = readIncomeGem(image=images[i], model=model, metadata=metadata)
        incomestatement.update(isPageInfo)
    return incomestatement

def process_cashflow(images, cfPage, model, metadata):
    cashflow = dict()
    for i in range(cfPage[0], cfPage[1] + 1):
        cfPageInfo = readCashflowGem(image=images[i], model=model, metadata=metadata)
        cashflow.update(cfPageInfo)
    return cashflow


