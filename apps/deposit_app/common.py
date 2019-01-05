from ..initdb import Base, engine, db_session
from apps.deposit_app.models import Account,Transaction,User
from ..ulib import obj_to_dict,add_Decimal,sub_Decimal,mul_Decimal,div_Decimal
from decimal import * 
getcontext().prec = 12  


def checkExistedAccount(user_id,currency):
    with db_session() as session:
        check_account = session.query(Account).filter(Account.user_id == user_id, Account.currency == currency).all()
        
        if(len(check_account)==0):
            return False
    return True

def checkVolumeTranfer(currency,volume,balance):
    if(currency == "VND" and Decimal(volume) > 25000):
        return False,"Max volume with VND is 25000 USD/transaction!"
    if(currency == "BTC" and Decimal(volume) > 2.5):
        return False,"Max volume with BTC is 2.5 btc/transaction!"
    if(currency == "USDT" and Decimal(volume) > 50000):
        return False,"Max volume with USDT is 2.5 btc/transaction!"
    if(currency == "ETH" and Decimal(volume) > 50000):
        return False,"Max volume with ETH is 2.5 btc/transaction !"
    checked = add_Decimal(balance,volume)
    if(checked < 0):
        return False,"Value withdraw bigger balance account!"
    return True,"Volume tranfer is accept!"

def checkCurrencyTransaction(user_id, currency):
    with db_session() as session:
        check_account = session.query(Account).filter(Account.user_id == user_id, Account.currency == currency).first()
        if(check_account is None):
            return False
    return True
def addcreateat(row):
    x = Transaction.to_dict(row)
    print(row.createAt)
    x["createAt"]=str(row.createAt) 
    return x
def addUsername(row):
    x = Transaction.to_dict(row)
    with db_session() as session:
        print(x["user_id"])
        user = session.query(User).filter(User.id == x["user_id"]).first()
        print(user)
        x['user_name'] = user.username
        x['phone'] = user.phone
        x['email'] = user.email
        account = session.query(Account).filter(Account.account_no == x["account_no"]).first()
        x["account_type"] = account.type
        x["account_balance"] = account.balance
        x["address_destination"]= ""
        x["createAt"]=str(row.createAt) 
    
    return x


