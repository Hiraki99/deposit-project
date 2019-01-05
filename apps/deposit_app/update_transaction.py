from . import Micro, celery
import traceback
from apps.deposit_app.models import Account, Transaction, MessageBanking,User,BankingAccount,RootKey
from . import db_session
from ..ulib import obj_to_dict
from sqlalchemy import asc, desc
# open account
import uuid
import random
from sqlalchemy import func
from sqlalchemy.sql import label
import sys
import datetime
import requests
from datetime import timedelta
from decimal import *
from . import config
from celery import Celery
from celery.schedules import crontab
from ..ulib import add_Decimal,sub_Decimal
from ..ulib import obj_to_dict,add_Decimal,sub_Decimal,mul_Decimal,div_Decimal
from .config import socketio
root_key_id = 13
from socketIO_client import SocketIO, LoggingNamespace
from .socket_client import MainNamespace
# import config from file
from configparser import ConfigParser
config = ConfigParser()
config.read('config.env')

with db_session() as session:
    root = session.query(RootKey).order_by(RootKey.id.desc()).first()
    root_key_id = root.wallet_id


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(minute='*/1'),
        getAllSubkey.s()
    )

@celery.task
def getAllSubkey():
    with db_session() as session:
        all_account = session.query(Account).filter(Account.currency!= 'VND').all()
        
        for item_account in all_account:
            
            payload = {
                "root_key_id" : root_key_id,
                "subkey_id" : item_account.subkey_id
            }
            
            lastest_transaction_id = item_account.lastest_transaction_id

            # luu lai transaction id moi nhat vs moi account

            result = requests.post(config["ENV"]["hdwallet"] + "updateTransaction", json=payload )
            all_transaction = result.json()
            
            for item_transaction in all_transaction:
                # kiem tra vs lastest transaction cua moi account sau do cap nhap id transaction moi nhat vao cua cac account
                if(item_transaction["transaction_id"] > lastest_transaction_id):
                    try:
                        kind = "with"
                        status = 0
                        description = "This is withdraw "+ item_account.currency
                        deposit_method = item_account.currency + " withdraw"
                        if(not item_transaction["spent"]):
                            kind="depo"
                            description = "This is deposit "+ item_account.currency
                            deposit_method = item_account.currency + " depo"
                        if(item_transaction["status"] == "confirmed"):
                            status =1
                        _, amount = div_Decimal(item_transaction["value"], 100000000)
                        print(amount)
                        new_transaction = Transaction(item_account.subkey,item_account.user_id, item_account.id, item_account.account_no, kind,
                                        "", deposit_method, item_account.type, description, item_account.currency, 
                                        amount, status)   
                        session.add(new_transaction)
                        if(kind == "depo"):
                            item_account.balance = add_Decimal(item_account.balance,amount)
                        else:
                            item_account.balance = sub_Decimal(item_account.balance,amount)
                            amount = mul_Decimal(-1 , amount)
                        

                        socketio.emit("update_amount_crypto",{"amount":amount,"currency": item_account.currency,"balance": item_account.balance})
                        socketPreTrade = SocketIO(config["ENV"]['PRE_TRADE'], config["ENV"]['PORT_PRE_TRADE'])

                        socketclient = socketPreTrade.define(MainNamespace, '/pre_trade/order')
                        
                        socketclient.emit("update-mem",{"UserID": item_account.user_id,"currency": item_account.currency,"amount" : amount})
                    except:
                        pass
                    
            if(len(all_transaction) > 0):
                print(all_transaction[0]["transaction_id"] )
                item_account.lastest_transaction_id = int(all_transaction[0]["transaction_id"] )
                session.add(item_account)
            

@celery.task
def UpdateBalaceDepositVND():
    with db_session() as session:
        all_account = session.query(Account).filter(Account.currency== 'VND').all()
        
        for item_account in all_account:
            user = session.query(User).filter(User.id == item_account.user_id).first()
            
            payload = {
                "phone" : user.phone
            }
            # luu lai transaction id moi nhat vs moi account

            result = requests.post(config["ENV"]["HOST_GMS"] + "/get-message", json=payload )
            message_client = result.json()
            if(message_client["status"] ==1):
                message_server = session.query(MessageBanking).filter(MessageBanking.Code == message_client["code"], MessageBanking.live == True).first()
                # Check code existed
                if(message_server is None or message_server.live == False):
                    continue
                # Check banking
                banking = session.query(BankingAccount).filter(item_account.account_no).first()
                if(banking is None or banking.number_bank_card != message_client["number_bank_card"]):
                    continue
                content = message_client["content"]
                amount = message_client["amount"]
                message_server.ContentMessage = content
                message_server.live = False

                deposit_method = item_account.currency + " depo"
                new_transaction = Transaction(item_account.subkey,item_account.user_id, item_account.id, item_account.account_no, "depo",
                                "", deposit_method, item_account.type, content, item_account.currency,amount, 1)
                item_account.balance = add_Decimal(item_account.balance,amount)
                session.add(message_server)
                session.add(new_transaction)
                session.add(item_account)
                print("Update new balance Success " +  item_account.account_no)
            else:
                print("No message for " +  item_account.account_no)


            
            
            
            
        