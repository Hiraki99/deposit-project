from . import Micro, celery
import traceback
from apps.deposit_app.models import Account, Transaction,BankingAccount,User, ExecutionReport, MessageBanking,RootKey, MasterKey
from . import db_session
from ..ulib import obj_to_dict,add_Decimal,sub_Decimal,mul_Decimal,div_Decimal
from apps.deposit_app import common
from sqlalchemy import asc, desc
from .process import updateAll,random_code,check_new_code

# open account
import uuid
import random
from sqlalchemy import func
from sqlalchemy.sql import label
import sys
import datetime
import requests
# from datetime import datetime
from . import config
from decimal import *
from random import randint
from flask_socketio import emit
from .config import socketio
from socketIO_client import SocketIO, LoggingNamespace
from .socket_client import MainNamespace

from configparser import ConfigParser
config = ConfigParser()
config.read('config.env')



getcontext().prec = 8

with db_session() as session:
    root = session.query(RootKey).order_by(RootKey.id.desc()).first()
    root_key_id = root.wallet_id
    # master btc
    master_btc = session.query(MasterKey).filter(MasterKey.currency == 'BTC').first()
    master_key_id_btc = master_btc.account_id
    # master eth
    master_eth = session.query(MasterKey).filter(MasterKey.currency == 'ETH').first()
    master_key_id_eth = master_eth.account_id
    # master usdt
    master_usdt = session.query(MasterKey).filter(MasterKey.currency == 'USDT').first()
    master_key_id_usdt = master_usdt.account_id

# master_key_id_btc = 5
# master_key_id_eth = 6
# master_key_id_usdt = 7
# root_key_id = 13

area_code = "084"

patition_code = "01-01-01"

@celery.task
def celery_open_withdraw_request(transaction_id):
    try:
        with db_session() as session:
            new_transaction = session.query(Transaction).filter(
                Transaction.id == transaction_id).first()
            account = session.query(Account).filter(
                Account.account_no == new_transaction.account_no).first()
            account.balance = add_Decimal(account.balance, new_transaction.value)

            session.add(new_transaction)
            session.add(account)
            print("Add transaction withdraw success")
        pass
    except:
        pass

@Micro.typing('/exister-account-currency')
@Micro.json
def check_existed_account(user_id=None,currency=None):
    try:
        with db_session() as session:
            account = session.query(Account).filter(Account.user_id ==user_id, Account.currency == currency).first()
            if(account is None):
                return  {"status" : 1}
            else:
                return {
                    "status" : 0,
                    "message": "Existed Account"
                }
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Check Existed Account error"
}
@Micro.typing('/account/open')
@Micro.json
def open_account(user_id=None, type='0001', description='', currency='VND', balance=0.0):
    """Use for open new account => will insert a row in Account table

    Arguments:
        user_id {[type]} -- [description]
        account_no {[type]} -- [description]



    Keyword Arguments:
        type {str} -- [description] (default: {'0001'})
        description {str} -- [description] (default: {''})
        currency {str} -- [description] (default: {'VND'})
        balance {float} -- [description] (default: {0.0})

    Example json accept:
        {
            "user_id":1,
            "account_no":"000129485",
            "type":"0001",
            "description":"This is open account",
            "currency":"VND",
            "balance":0.0,
        }
    result
        {
            "account": {
                "account_no": "c3e6145a783411e88475dc85de91ce85", 
                "balance": 0, 
                "currency": "BTC", 
                "description": "", 
                "subkey": "4c45523b8bf54955aa9a93a9bc41d035", 
                "type": "0001", 
                "user_id": 1
            }, 
            "message": "insert success", 
            "status": 1
        }
    """
    data = {}
    try:
        if(common.checkExistedAccount(user_id, currency)):
            data["status"] = 0
            data["message"] = "existed account"
        else:
            
            account_no = area_code + "-" + patition_code+"-"+format(random.randint(0,9999999), '07d')
            description = "This is open account "+ currency
            with db_session() as session:
                new_account = Account(user_id, account_no,
                                    type, description, currency, balance)
                session.add(new_account)
                session.flush()

                payload = {
                    "root_key_id" : root_key_id
                }
                
                if(currency == "BTC"):
                    payload['master_key_id'] = master_key_id_btc
                if(currency == "ETH"):
                    payload['master_key_id'] = master_key_id_eth
                if(currency == "USDT"):
                    payload['master_key_id'] = master_key_id_usdt
                print("account no %s"%account_no)

                if(currency != "VND"):
                    payload["useraccount_id"] = new_account.id
                    result = requests.post(config["ENV"]["hdwallet"] + "create_new_subkey", json=payload)

                    subkey = result.json()["subkey_info"]
                    new_account.subkey = subkey["address"]
                    new_account.balance = subkey["balance"]
                    new_account.subkey_id = subkey["key_id"]
                    new_account.lastest_transaction_id = 0
                    session.add(new_account)

                data["account"] = obj_to_dict(new_account)
                
            data["status"] = 1
            data["message"] = "insert success"
    except:
        traceback.print_exc()
        data["status"] = 0
        data["message"] = "insert fail"
        pass
    return data


@Micro.typing('/account/process', methods='POST')
@Micro.json
def process_account_request(parameter_list):
    pass


@Micro.typing('/account/hide')
@Micro.json
def hide_account(account_no=None, hide=None):
    data = {}
    try:
        with db_session() as session:
            account = session.query(Account).filter(
                Account.account_no == account_no).first()
            
            account.live = hide
            session.add(account)
            session.flush()
            data["status"] = 1
            data["message"] = "update account success"
    except:
        traceback.print_exc()
        data["status"] = 0
        data["message"] = "update account fail"
        pass
    return data


@Micro.typing('/account/info/view')
@Micro.json
def view_account_info(account_no=None):
    """Use for view all info of account

    Returns:
        [type] -- [description]
    """
    data = {}
    try:
        with db_session() as session:
            account = session.query(Account).filter(
                Account.account_no == account_no).first()

            data["account"] = obj_to_dict(account)
            data["status"] = 1
            data["message"] = "query success"
    except:
        traceback.print_exc()
        data["status"] = 0
        data["message"] = "query fail"
        pass
    return data

# view account balance


@Micro.typing('/account/balance/view')
@Micro.json
def view_account_balance(user_id=None):
    """Use for view balance of all account

    Returns:
        [type] -- [description]
    """
    data = {}
    try:
        with db_session() as session:
            account = session.query(Account).filter(
                Account.user_id == user_id).all()
            data["account"] = {}
            data["existedBanking"] = False
            for row in account:
                # item = {}
                # item[row.currency] = 
                data["account"][row.currency] = Account.to_dict(row)  
                data["account"][row.currency]["avaiable"] = data["account"][row.currency]["balance"]
                data["account"][row.currency]["in_order"] = 0
                data["account"][row.currency]["value"] = 0
                if(row.currency == "VND"):
                    banking = session.query(BankingAccount).filter(BankingAccount.account_no == row.account_no).first()
                    # print(BankingAccount.to_dict(banking))
                    if(banking is not None):
                        data["banking"] = BankingAccount.to_dict(banking)
                        data["existedBanking"] = True
            data["account"] = updateAll(data["account"],user_id)
            data["status"] = 1
            data["message"] = "query success"
    except:
        traceback.print_exc()
        data["status"] = 0
        data["message"] = "query fail"
        pass
    return data

# view all account with all user id

# view account balance
@Micro.typing('/getAll/balance/view')
@Micro.json
def getAll():
    """Use for view balance of all account

    Returns:
        [type] -- [description]
    """
    res = {
        "arr" : {}
    }
    try:
        with db_session() as session:
            all_user = session.query(User).all()
            item = {}
            for user in all_user:
                account = session.query(Account).filter(Account.user_id == user.id).all()
                item[user.id] = {}
                for row in account:
                    item[user.id][row.currency] = {
                        "account_no" : row.account_no,
                        "balance" : row.balance,
                        "currency" : row.currency,
                        "avaiable" : row.balance,
                        "orderID" : []
                    }
            res["arr"] = item
        res["status"] =1            
    except:
        traceback.print_exc()
        res["status"] = 0
    return res

# view account history

@Micro.typing('/account/history/view')
@Micro.json
def view_account_history(account_no=None):
    """Use for view all transaction history of an account. all deposit and withdraw

    Returns:
        [user_id] -- [description]
    """
    data = {}
    try:
        with db_session() as session:
            all_transaction = session.query(Transaction).filter(
                Transaction.account_no == account_no).all()

            if len(all_transaction) == 0:
                data["transaction"] = []
                data["balance_VND"] = 0.0
                data["balance_BTC"] = 0.0
                data["balance_ETH"] = 0.0
            else:
                all_currency = session.query(Transaction.currency, label(
                    "total_balance", func.sum(Transaction.value))).group_by(Transaction.currency).all()

                for all_btc in all_currency:

                    data["balance_"+all_btc.currency] = all_btc.total_balance
                data["transaction"] = [common.addcreateat(
                    row) for row in all_transaction]

            data["status"] = 1
    except:
        traceback.print_exc()
        data["status"] = 0
        pass
    return data


@Micro.typing('/account/history')
@Micro.json
def view_user_history(user_id=None, kind="depo"):
    """Use for view all transaction history of an account. all deposit and withdraw

    Returns:
        [user_id] -- [description]
    """
    data = {}
    try:
        with db_session() as session:
            all_transaction = session.query(Transaction).filter(Transaction.user_id == user_id).order_by(desc(Transaction.createAt)).limit(100).all()
            all_report = session.query(ExecutionReport).filter(ExecutionReport.live == True, ExecutionReport.UserID == user_id).order_by(desc(ExecutionReport.TransactTime)).limit(100)
            if len(all_transaction) == 0:
                data["transaction"] = []
            else:
                data["transaction"] = [common.addcreateat(
                    row) for row in all_transaction]
            result = []
            for row in all_report:
                # print(row.TransactTime)
                item = ExecutionReport.to_dict(row)
                item["TransactTime"] = str(row.TransactTime.strftime("%c"))
                result.append(item)
            data["transaction_trading"] = result
            data["status"] = 1
            data["lala"] ="lala"
    except:
        traceback.print_exc()
        data["status"] = 0
        pass
    return data

# deposit money


@Micro.typing('/deposit/open')
@Micro.json
def open_deposit_request(to,user_id=None,  kind='depo', approver_name='', deposit_method='bank_transfer', type='0001', description='', currency='VND', value=0.0, status=0):
    """Use for deposit to an account

    Keyword Arguments:
        user_id {[type]} -- [description] (default: {None})
        account_id {[type]} -- [description] (default: {None})
        account_no {[type]} -- [description] (default: {None})
        approver_name {str} -- [description] (default: {''})
        deposit_method {str} -- [description] (default: {'bank_transfer'})
        type {str} -- [description] (default: {'0001'})
        description {str} -- [description] (default: {''})
        currency {str} -- [description] (default: {'VND'})
        value {float} -- [description] (default: {0.0})
        status {int} -- [description] (default: {0})
    Example json:
        {
            "user_id": 132,
            "account_id": 100,
            "account_no": "091823829" # no more than 12 string,
            "kind":"depo",
            "approver_name": "",
            "deposit_method": "bank_transfer",
            "type": "0001",
            "description": "Test deposit",
            "currency": "VND",
            "value": 1000.5,
            "status": "0",
        }
    """

    data = {}
    if(Decimal(value) <= 0 or kind != 'depo'):
        data["status"] = 0
        data["message"] = "Transaction deposit error, volume deposit must positive Or Type Transaction Error"
        return data
    if(not common.checkCurrencyTransaction(user_id, currency)):
        data["status"] = 0
        data["message"] = "Type currency don't match with account"
        return data

    try:
        with db_session() as session:
            account = session.query(Account).filter(
                Account.user_id == user_id, Account.currency == currency).first()
            new_transaction = Transaction(to,user_id, account.account_id, account.account_no, kind,
                                          approver_name, deposit_method, type, description, currency, value, status)
            
            account.balance = add_Decimal(account.balance, value)


            session.add(new_transaction)
            session.add(account)

            data["status"] = 1
            data["balance_account"] = str(account.balance)
            data["transaction"] = obj_to_dict(new_transaction)
            data["transaction"]["createAt"] = str(datetime.datetime.now())
    except:
        traceback.print_exc()
        data["status"] = 0
        pass
    return data


@Micro.typing('/deposit/cancel', methods='POST')
@Micro.json
def cancel_deposit_request(parameter_list):
    pass


@Micro.typing('/deposit/view')
@Micro.json
def view_deposit_request(id=None):
    """Use for view deposit request by account

    Keyword Arguments:
        account_no {[type]} -- [description] (default: {None})
    """

    data = {}
    try:
        with db_session() as session:
            transaction_deposit = session.query(
                Transaction).filter(Transaction.id == id).first()

            data["transaction"] = obj_to_dict(transaction_deposit)
            data["transaction"]["createAt"] = str(transaction_deposit.createAt)
            data["status"] = 1
    except:
        traceback.print_exc()
        data["status"] = 0
        pass
    return data


@Micro.typing('/deposit/process', methods='POST')
@Micro.json
def process_deposit_request(parameter_list):
    pass

# withdraw money


@Micro.typing('/withdraw/open')
@Micro.json
def open_withdraw_request(to=None,user_id=None, kind='with', approver_name='', deposit_method='bank_transfer', type='0001', description='', currency='VND', value=0.0, status=0):
    """Use for deposit to an account

    Keyword Arguments:
        to {[type]} -- [description] (default: {None})
        user_id {[type]} -- [description] (default: {None})
        account_id {[type]} -- [description] (default: {None})
        account_no {[type]} -- [description] (default: {None})
        approver_name {str} -- [description] (default: {''})
        deposit_method {str} -- [description] (default: {'bank_transfer'})
        type {str} -- [description] (default: {'0001'})
        description {str} -- [description] (default: {''})
        currency {str} -- [description] (default: {'VND'})
        value {float} -- [description] (default: {0.0})
        status {int} -- [description] (default: {0})
    Example json:
        {
            "to" : "mpmGb2V1Mke6YfRiy5oTRT3aRhxfmuzSje"
            "user_id": 132,
            "account_id": 100,
            "account_no": "091823829" # no more than 12 string,
            "kind":"with",
            "approver_name": "",
            "deposit_method": "bank_transfer",
            "type": "0001",
            "description": "Test withdraw",
            "currency": "VND",
            "value": -100.5,
            "status": "0",
        }
    """
    data = {}
    
    try:
        if(to == None and currency == "VND"):
            data["status"] = 0
            data["message"] = "Transaction withdraw error, don't have address to"
            return data
        if(Decimal(value) > 0 or kind != 'with'):
            data["status"] = 0
            data["message"] = "Transaction withdraw error, volume withdraw must negative Or Type Transaction Error"
            return data
        if(not common.checkCurrencyTransaction(user_id, currency)):
            data["status"] = 0
            data["message"] = "Type currency don't match with account"
            return data
        with db_session() as session:
            account = session.query(Account).filter(
                Account.user_id == user_id,Account.currency == currency).first()
            checked, message = common.checkVolumeTranfer(
                currency, value, account.balance)
            if(not checked):
                data["status"] = 0
                data["message"] = message
            else:
                data["status"] = 1
                data["message"] = "Transaction withdraw success"
                data["transaction"] = []
                with db_session() as session:
                    new_transaction = Transaction(to,user_id, account.id, account.account_no,
                        kind, approver_name, deposit_method, type, description, currency, value, status)
                    session.add(new_transaction)
                    item = obj_to_dict(new_transaction)
                    item["createAt"] = str(datetime.datetime.now())
                    data["transaction"].append(item)
                    celery_open_withdraw_request.apply_async(
                        args=[new_transaction.id], countdown=10)

    except:
        traceback.print_exc()
        data["status"] = 0
        data["message"] = "Transaction withdraw fail"
        pass
    return data


@Micro.typing('/withdraw/cancel', methods='POST')
@Micro.json
def cancel_withdraw_request():
    pass

@Micro.typing('/withdraw/all_transaction')
@Micro.json
def getallwithdraw(kind = 'with'):
    data = {}
    try:
        with db_session() as session:
            transaction_withdraw = session.query(Transaction).filter(Transaction.kind == kind).all()
            data["status"] =1
            data["transaction"] = [common.addUsername(
                        row) for row in transaction_withdraw]
    except:
        traceback.print_exc()
        data["status"] =0
    
    return data

@Micro.typing('/withdraw/view', methods='GET')
@Micro.json
def view_withdraw_request(id=None):
    data = {}
    try:

        with db_session() as session:
            transaction_deposit = session.query(
                Transaction).filter(Transaction.id == id).first()
            data["transaction"] = obj_to_dict(transaction_deposit)
            data["status"] = 1
    except:
        traceback.print_exc()
        data["status"] = 0
        pass
    return data


@Micro.typing('/withdraw/process', methods='POST')
@Micro.json
def process_withdraw_request(parameter_list):
    pass

@Micro.typing('/exister-banking')
@Micro.json
def check_existed_banking(user_id=None,currency=None):
    try:
        with db_session() as session:
            
            account = session.query(Account).filter(Account.user_id == user_id, Account.currency == currency).first()
            bank = session.query(BankingAccount).filter(BankingAccount.account_no == account.account_no).first()
            if(bank is None):
                return  {"status" : 1}
            else:
                return {
                    "status" : 0,
                    "message": "Existed Account"
                }
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Check Existed Account error"
        }

@Micro.typing('/new-banking')
@Micro.json
def new_banking(user_id,bank_name,bank_address,number_bank_card,fullname_bank_card):
    try:
        with db_session() as session:
            account = session.query(Account).filter(Account.user_id == user_id, Account.currency=="VND").first()
            new_banking = BankingAccount(bank_name,bank_address,number_bank_card,fullname_bank_card,account.account_no)
            session.add(new_banking)
            return {
                "status" : 1,
                "message": "Add new banking account error"
            }

    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Add new banking account error"
        }
    
@Micro.typing('/transaction_reports')
@Micro.json
def transaction_reports(Account_no=None,AllocAccount_no=None,AllocQty=None,Quantity=None):
    try:
        with db_session() as session:
            account = session.query(Account).filter(Account.account_no == Account_no).first()
            allocaccount = session.query(Account).filter(Account.account_no == AllocAccount_no).first()
            account.balance = sub_Decimal(account.balance, Quantity) 
            allocaccount.balance = add_Decimal(allocaccount.balance,AllocQty)
            session.add(account)
            session.add(allocaccount)
            return {
                "status": 1,
                "account" : Account.to_dict(account),
                "allocaccount" : Account.to_dict(allocaccount)
            }
            
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Update Balance Error"
        } 

@Micro.typing('/get-key-confirmation')
@Micro.json
def getKeyConfirm(user_id=None,currency='VND',account_no=None ):
    try:
        now=datetime.datetime.now().timestamp() 
        print("now= ",now)
        with db_session() as session:
            user= session.query(User).filter(User.id == user_id).first()
            account = session.query(Account).filter(Account.user_id == user_id, Account.currency == currency).first()
            message_server = session.query(MessageBanking).filter(MessageBanking.Account_no == account.account_no, MessageBanking.live == True).first()
            if(message_server is None):
                code = "#"+ random_code()
                contentMessage = "Key verify "+code
                banking = session.query(BankingAccount).filter(BankingAccount.account_no == account.account_no).first()
                messageBanking = {}
                if(banking is None):    
                    messageBanking = MessageBanking(code, contentMessage,1,user.phone,currency,account.account_no,"") 
                    session.add(messageBanking)
                else:
                    messageBanking = MessageBanking(code, contentMessage,1,user.phone,currency,account.account_no,banking.number_bank_card) 
                    session.add(messageBanking)
                return {
                    "status": 1,
                    "message": "New Code",
                    "key_confirm": code,
                    "time_countdown" : int(config['ENV']['TIME_COUNTDOWN_CODE'])
                }
            elif(message_server.createAt.timestamp() + int(config['ENV']['TIME_COUNTDOWN_CODE']) <= int(datetime.datetime.now().timestamp())):
                session.delete(message_server)
                code = "#"+ random_code()
                contentMessage = "Key verify "+code
                banking = session.query(BankingAccount).filter(BankingAccount.account_no == account.account_no).first()
                messageBanking = {}
                if(banking is None):    
                    messageBanking = MessageBanking(code, contentMessage,1,user.phone,currency,account.account_no,"") 
                    session.add(messageBanking)
                else:
                    messageBanking = MessageBanking(code, contentMessage,1,user.phone,currency,account.account_no,banking.number_bank_card) 
                    session.add(messageBanking)
                print("messageBanking.createAt.timestamp()11 = ",messageBanking)
                
                return {
                    "status": 1,
                    "message": "New Code",
                    "key_confirm" : code,
                    "time_countdown" : int(config['ENV']['TIME_COUNTDOWN_CODE'])
                }
            else:
                return {
                    "status" : 1,
                    "message": "old code",
                    "key_confirm" : message_server.Code,
                    "time_countdown" : int(config['ENV']['TIME_COUNTDOWN_CODE']) - (int(datetime.datetime.now().timestamp()) - int(message_server.createAt.timestamp()))
                }
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Fault Server, Please take again"
        } 
    
@Micro.typing('/key-confirmation')
@Micro.json
def getNewKeyConfirm(user_id=None,currency='VND',account_no=None ):
    try:
        with db_session() as session:
            user= session.query(User).filter(User.id == user_id).first()
            account = session.query(Account).filter(Account.user_id == user_id, Account.currency == currency).first()
            banking = session.query(BankingAccount).filter(BankingAccount.account_no == account.account_no).first()
            code = "#"+ random_code()        
            message_server = session.query(MessageBanking).filter(MessageBanking.Account_no == account.account_no, MessageBanking.live == True).first()
            old_code = message_server.Code
            if(message_server is not None):
                session.delete(message_server)

            contentMessage = "Key verify "+code
            messageBanking = {}
            if(banking is None):    
                messageBanking = MessageBanking(code, contentMessage,1,user.phone,currency,account.account_no,"") 
            else:
                messageBanking = MessageBanking(code, contentMessage,1,user.phone,currency,account.account_no,banking.number_bank_card) 
            
            session.add(messageBanking)
            
            return {
                "status" : 1,
                "key_confirm" : code,
                "old_code" : old_code,
                "time_countdown" : int(config['ENV']['TIME_COUNTDOWN_CODE'])
            }
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Fault Server, Please take again"
        } 
# @socketio.on('init-socket', namespace='/deposit')
@Micro.typing('/confirm-message')
@Micro.json
def confirmMessage(amount=None,content =None,code=None ):
    try:
        with db_session() as session:
            
            message_server = session.query(MessageBanking).filter(MessageBanking.Code == code, MessageBanking.live == True).first()
            if(message_server is None):
                return {
                    "status" : 0,
                    "message": "Code expired %r"%code
                }
            item_account = session.query(Account).filter(Account.account_no == message_server.Account_no).first()
                # Check code existed
            
            # Check banking
            banking = session.query(BankingAccount).filter(BankingAccount.account_no == item_account.account_no).first()
            print("banking")
            
            user= session.query(User).filter(User.id == item_account.user_id).first()

            

            deposit_method = item_account.currency + " depo"
            new_transaction = Transaction(item_account.subkey,item_account.user_id, item_account.id, item_account.account_no, "depo",
                            "", deposit_method, item_account.type, content, item_account.currency,amount, 1)
            print(amount)
            item_account.balance = add_Decimal(item_account.balance,amount)
            
            session.add(new_transaction)
            session.add(item_account)
            session.flush()

            message_server.ContentMessage = content
            message_server.live = False
            message_server.TransactionID = new_transaction.id
            session.add(message_server)

            # Add New Key For User
            
            new_code = "#"+ random_code()
            
            new_contentMessage = "Key verify "+new_code
            if(banking is None):    
                messageBanking = MessageBanking(new_code, new_contentMessage,1,user.phone,item_account.currency,item_account.account_no,"") 
            else:
                messageBanking = MessageBanking(new_code, new_contentMessage,1,user.phone,item_account.currency,item_account.account_no,banking.number_bank_card) 
            
            session.add(messageBanking)

            socketio.emit("code-used",{"old_code":code,"new_code": new_code,"amount":amount,"balance": item_account.balance})
            
            socketPreTrade = SocketIO(config["ENV"]['PRE_TRADE'], config["ENV"]['PORT_PRE_TRADE'])

            socketclient = socketPreTrade.define(MainNamespace, '/pre_trade/order')
            socketclient.emit("update-mem",{"UserID": item_account.user_id,"currency": item_account.currency,"amount" : amount})
            return {
                    "status" : 1,
                    "message" : "update Balance %r Success"%item_account.account_no ,
                    "transactionid":  new_transaction.id
                }
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "Update Balance Error"
        } 
@Micro.typing('/total-daily-transaction')
@Micro.json
def total_daily_transaction():
    try:
        now = datetime.datetime.now().timestamp()
        with db_session() as session:
            list_tran = session.query(Transaction).filter(Transaction.live==True).all()
            list_report = session.query(ExecutionReport).filter(ExecutionReport.live==True).all()
            count = 0
            for row in list_tran:
                if row.createAt.timestamp() + 86000 >= now:
                    count=count+1
            for row in list_report:
                if row.createAt.timestamp() + 86000 >= now:
                    count=count+1
            # print("total_daily_transaction ok count = ",count)
            return {
                "status" : 1,
                "message": "get daily transaction ok",
                "total_daily_transaction": count
            }
    except:
        traceback.print_exc()
        return {
            "status" : 0,
            "message": "get daily transaction failed"
        }

