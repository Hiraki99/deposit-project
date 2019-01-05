from ..ulib import div_Decimal,sub_Decimal, add_Decimal,mul_Decimal
from .models import Account, Transaction,BankingAccount,User, ExecutionReport, MessageBanking
from . import db_session
from random import randint
import random

def updateItem(json, order):
    
    pair = order["Symbol"].split("/")
   

    if(order["Side"] == "Buy"):
        Account = pair[1]
        AllocAccount = pair[0]
        volume_account = mul_Decimal(order["OrderQty"],order["Price"])
    if(order["Side"] == "Sell"):
        Account = pair[0]
        AllocAccount = pair[1]
        volume_account = order["OrderQty"]
    print(Account)
    print(AllocAccount)
    # Check account currency existed in user id
    if(Account in json and AllocAccount in json):
        
        if((json[Account]["account_no"] == order["Account"] )):
            print((json[Account]["account_no"] == order["Account"] ))
            
            
            print(volume_account)
            
    
            json[Account]["avaiable"] = sub_Decimal(json[Account]["avaiable"],volume_account)
            json[Account]["in_order"] = add_Decimal(json[Account]["in_order"],volume_account)
            json[Account]["value"] = add_Decimal(json[Account]["value"],volume_account)

            print(json[Account]["avaiable"])
    return json
                
def updateAll(json,user_id):
    """[summary]
    
    Arguments:
        json {[json]} -- [all info Account, Balance, Avaiable , List Order of Account]
    
    Returns:
        [json] -- [All info Account currency with list order in mem (order dont match) ]
    """
    with db_session() as session:
        # Step1 : Add all order in account, have all order (match and dont't match), update balance
        AllOrder = session.query(ExecutionReport).filter(ExecutionReport.OrdStatus == "New", ExecutionReport.UserID ==user_id, ExecutionReport.live == True).all()
        for item in AllOrder:
            # print(ExecutionReport.to_dict(item))
            item = ExecutionReport.to_dict(item)
            json = updateItem(json,item)
            # break
    
    return json

def check_new_code(new_code):
    try:
        with db_session() as session:
            message_server = session.query(MessageBanking).filter(MessageBanking.Code == new_code).first()
            if(message_server is None):
                return True
        return False
    except:
        return False

# def random_code():
#     characters = "0123456789abcdefghiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
#     tmp = ""
#     for i in range(0,7):
#         tmp += characters[randint(0,len(characters)-1)]
#     return str(tmp)


def digits(ndigits=8, code_cast_func=str):
    """
    Digits verification code, default 8 digits string.
    ``ndigits`` indicates the length of the code to return.
    ``code_cast_func`` a callable used to cast the code return value.
    """
    return code_cast_func(random.randrange(10 ** (ndigits - 1), 10 ** ndigits))

random_code = digits
