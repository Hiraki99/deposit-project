from sqlalchemy import ForeignKey
from sqlalchemy import asc, desc, func
from sqlalchemy.sql.expression import and_, or_, exists
from sqlalchemy import Column, Integer, Unicode, String, DateTime, Boolean, Numeric, Text, Date, UniqueConstraint, UnicodeText, Index, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import json
import datetime
from . import Base, db_session
import uuid, random
from ..ulib import obj_to_dict
from passlib.apps import custom_app_context as pwd_context


class BaseModel(object):
    __tablename__ = 'BaseModel'
    id = Column(Integer, primary_key=True)
    live = Column(Boolean,  nullable=False, default=True)
    createAt = Column(DateTime,   nullable=False, default=datetime.datetime.now, index=True)

    @staticmethod
    def to_dict(row):
        d = obj_to_dict(row)
        return d

    def __repr__(self):
        return '<%s is: id= %r>' % (self.__tablename__, self.id)


class Account(BaseModel, Base):
    __tablename__ = 'Account'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer)
    account_no = Column(String(32), unique=True, nullable=False)
    subkey = Column(String(255),  nullable=False, index=True)
    description = Column(String(255),  nullable=False)
    type = Column(String(10),  nullable=False, index=True)
    currency = Column(String(10),  nullable=False, index=True)
    balance = Column(Float, nullable=False, default=0, index=True)
    subkey_id = Column(Integer, nullable=False)
    lastest_transaction_id = Column(Integer, nullable=False)
    
    live = Column(Boolean,  nullable=False, default=True)
    createAt = Column(DateTime,   nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime,   nullable=False, default=datetime.datetime.now, index=True)

    def __init__(self, user_id, account_no, type='0001', description='', currency='VND', balance=0.0,subkey_id=0,lastest_transaction_id=0 ):
        self.user_id = user_id
        self.account_no = account_no
        self.subkey = uuid.uuid4().hex # will replace by real subkey later
        self.type = type
        self.description = description
        self.currency = currency
        self.balance = balance
        self.subkey_id = subkey_id
        self.lastest_transaction_id = lastest_transaction_id

    @staticmethod
    def view_account_all():
        with db_session() as session:
            list_query = session.query(Account).filter(
                Account.live == True).order_by(Account.createAt.desc())
            full_accs = [Account.to_dict(row) for row in list_query]
        return full_accs
    
    @staticmethod
    def view_account(account_no):
        with db_session() as session:
            list_query = session.query(Account).filter(Account.account_no == account_no,
                Account.live == True).order_by(Account.createAt.desc())
            full_accs = [Account.to_dict(row) for row in list_query]
        return full_accs
    
    @staticmethod
    def hide_account(parameter_list):
        pass

class BankingAccount(BaseModel, Base):
    __tablename__ = 'BankingAccount'

    id = Column(Integer, primary_key = True)
    bank_name = Column(String(255), nullable = False)
    bank_address = Column(String(255), nullable = False)
    number_bank_card = Column(String(255), nullable = False)
    fullname_bank_card = Column(String(255), nullable = False)
    account_no = Column(String(32),ForeignKey('Account.account_no'))
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    def __init__(self, bank_name, bank_address, number_bank_card,fullname_bank_card,account_no):
        self.bank_name = bank_name
        self.bank_address = bank_address
        self.number_bank_card = number_bank_card
        self.fullname_bank_card = fullname_bank_card
        self.account_no = account_no
    def __repr__(self):
        return '<Banking %r>' % self.bank_name


class Transaction(BaseModel, Base):
    __tablename__ = 'Transaction'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    account_id = Column(Integer)
    account_no = Column(String(32), nullable=False)
    approver_name = Column(String(255),nullable=False)

    # 'depo'-deposit, 'with'-withdraw
    kind = Column(String(4),  nullable=False, default='depo')

    type = Column(String(10),  nullable=False, index=True)
    currency = Column(String(10),  nullable=False, index=True)
    # will be negative if transfer money out of this account
    value = Column(Float,    nullable=False, default=0, index=True)
    description = Column(String(255),  nullable=False)
    deposit_method = Column(String(32),  nullable=False)
    
    transaction_hash = Column(String(500),  nullable=False)
    to = Column(String(500),  nullable=False)
    officer_id = Column(Integer,  nullable=False, default=1)
    # 0-Pending, 1-Unconfirmed, 2-In-progress, 4-Complete, 8-Cancelled
    status = Column(String(1),  nullable=False, default='0', index=True)
    live = Column(Boolean,  nullable=False, default=True)
    createAt = Column(DateTime,   nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime,   nullable=False, default=datetime.datetime.now, index=True)

    def __init__(self,to, user_id, account_id, account_no, kind='depo', approver_name='', deposit_method='bank_transfer', type='0001', description='', currency='VND', value=0.0, status=0,transaction_hash=''):
        # self.id = uuid.uuid1().hex
        self.to = to
        self.user_id = user_id
        self.account_no = account_no
        self.kind = kind
        self.approver_name = approver_name
        self.type = type
        self.description = description
        self.currency = currency
        self.value = value
        self.deposit_method = deposit_method
        self.status = status
        self.account_id = account_id
        self.transaction_hash = transaction_hash
    
    @staticmethod
    def view_account_transaction(parameter_list):
        pass

    @staticmethod
    def open_account_transactio(parameter_list):
        pass

    @staticmethod
    def cancel_account_transactio(parameter_list):
        pass

    @staticmethod
    def process_account_transactio(parameter_list):
        pass    

class User(BaseModel, Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), unique=True, nullable=False)
    password = Column(String(250), nullable=False)

    passwordresettoken = Column(String(250),default='')
    passwordresetexpires = Column(DateTime,default=datetime.datetime.utcnow)
    confirmed = Column(Boolean, default=False)
    confirmed_on = Column(DateTime)
    email = Column(String(250), unique=True, nullable=False)
    phone = Column(String(30), unique=True, nullable=False,default='')
    facebook = Column(String(250),default='')
    google = Column(String(250),default='')
    linkin = Column(String(250),default='')

    live = Column(Boolean, default=True, nullable=False)
    createAt = Column(DateTime, nullable=False,
                           default=datetime.datetime.utcnow)
    updateAt = Column(DateTime, nullable=False,
                           default=datetime.datetime.utcnow)
    
    role = Column(String(125), nullable=False)

    def __init__(self, username, password, email,role):
        """[Create New User for T-Rex]
        
        Arguments:
            username {[string]} -- [user name user login]
            password {[type]} -- [Password for user login]
            email {[type]} -- [Email regist t-rex exchange]
            role {[type]} -- [Role of user]
        """
        self.username = username
        self.password = password
        self.email = email
        self.role = role

    def __repr__(self):
        return '<User %r>' % self.username
    
    @staticmethod
    def hash_password(password):
        return pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

class ExecutionReport(BaseModel, Base):
    __tablename__ = 'ExecutionReport'

    id = Column(Integer, primary_key=True)
    # Account no
    Account = Column(String(40), nullable=False)
    ClOrdID = Column(String(40), nullable=False)
    OrderID = Column(String(40), nullable=False)
    DisplayName = Column(String(255), nullable=False)
    UserID = Column(Integer, nullable=False)
    OrigClOrdID = Column(String(40),nullable=False)
    OrderQty = Column(Float,nullable=False)
    LeavesQty= Column(Float,nullable=False)
    CumQty= Column(Float,nullable=False)
    OrdType = Column(String(40),nullable=False, default= "LO")
    OrdStatus = Column(String(40),nullable=False)
    Price = Column(Float,nullable=False)
    Symbol = Column(String(40), nullable=False, index=True)
    Side = Column(String(20), nullable=False, index=True)
    Currency = Column(String(20),  nullable=False, index=True)
    AllocSettlCurrency = Column(String(20),  nullable=False, index=True)
    TimeInForce = Column(String(20),  nullable=False, index=True)
    TransactTime = Column(DateTime, nullable=False, index=True)
    Commission = Column(Float,nullable=False)
    AllocAccount = Column(String(40), nullable=False, index=True)
    SecondaryOrderID = Column(String(40), nullable=False, index=True)
    execution_style = Column(String(40), nullable=False, index=True)
    
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)

    def __init__(self,Account=None,ClOrdID=None,OrderID=None,OrigClOrdID=None,OrderQty=None,LeavesQty=None,CumQty=None,OrdType=None,
                    OrdStatus=None,Price=None,Symbol=None,Side=None,Currency=None,AllocSettlCurrency=None,TimeInForce=None,TransactTime=None,
                    Commission=None, AllocAccount=None,SecondaryOrderID=None,execution_style=None,DisplayName=None, UserID=None):
        self.Account = Account
        self.ClOrdID = ClOrdID
        self.OrderID = OrderID
        self.OrigClOrdID = OrigClOrdID
        self.OrderQty = OrderQty
        self.LeavesQty = LeavesQty
        self.CumQty = CumQty
        self.OrdType = OrdType
        self.OrdStatus = OrdStatus
        self.Price = Price
        self.Symbol = Symbol
        self.Side = Side
        self.Currency = Currency
        self.AllocSettlCurrency = AllocSettlCurrency
        self.TimeInForce = TimeInForce
        self.TransactTime = TransactTime
        self.Commission = Commission
        self.AllocAccount = AllocAccount
        self.SecondaryOrderID = SecondaryOrderID
        self.execution_style = execution_style
        self.DisplayName = DisplayName
        self.UserID = UserID

class MessageBanking(BaseModel, Base):
    __tablename__ = 'MessageBanking'

    id = Column(Integer, primary_key=True)
    # Account no
    Code = Column(String(40), nullable=False)
    ContentMessage = Column(String(255), nullable=False)
    TransactionID = Column(Integer, nullable=False)
    Phone = Column(String(40),nullable=False)
    Currency=Column(String(40),nullable=False,default="VND")
    Account_no = Column(String(40),nullable=False)
    number_bank_card=Column(String(80),nullable=False)
    live = Column(Boolean,  nullable=False, default=True)
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)

    def __init__(self,Code=None,ContentMessage=None,TransactionID=None,Phone=None,Currency="VND",Account_no=None,number_bank_card=None):
        self.Code = Code
        self.ContentMessage = ContentMessage
        self.Phone = Phone
        self.TransactionID = TransactionID
        self.Currency = Currency
        self.Account_no= Account_no
        self.number_bank_card = number_bank_card

class RootKey(Base):
    __tablename__ = 'RootKey'

    id = Column(Integer, primary_key=True)
    main_network = Column(String(500), nullable=False)
    wallet_id= Column(Integer, unique=True,nullable=False)
    passphrase = Column(String(500),unique=True, nullable=False)
    scheme= Column(String(100),unique=True, nullable=False)
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    
    def __init__(self, main_network,wallet_id,passphrase,scheme):
        self.main_network = main_network
        self.wallet_id = wallet_id
        self.passphrase = passphrase
        self.scheme = scheme
    def __repr__(self):
        return '<NameGroRootKeyup %r>' % self.wallet_id

class MasterKey(Base):
    __tablename__ = 'MasterKey'

    id = Column(Integer, primary_key=True)
    address = Column(String(500),unique=True, nullable=False)
    key_private = Column(String(500),unique=True, nullable=False)
    key_public = Column(String(500),unique=True, nullable=False)
    wif = Column(String(500),unique=True, nullable=False)
    path = Column(String(500),unique=True, nullable=False)
    wallet_id_sqlite = Column(Integer, unique=True,nullable=False)
    balance = Column(Float,nullable=False, default=0)
    account_id= Column(Integer, unique=True, nullable=False)
    root_id = Column(Integer,nullable=False)
    currency = Column(String(500),unique=True, nullable=False)
    createAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)
    updateAt = Column(DateTime, nullable=False, default=datetime.datetime.now, index=True)

    def __init__(self, address, key_private,key_public,wif,path,wallet_id_sqlite,balance,root_id,account_id):
        self.address = address
        self.key_private = key_private
        self.key_public = key_public
        self.wif = wif
        self.path = path
        self.wallet_id_sqlite = wallet_id_sqlite
        self.balance = balance
        self.root_id = root_id
        self.account_id = account_id

    def __repr__(self):
        return '<NameGroup %r>' % self.address