import requests
from microservices_connector.Interservices import Microservice, SanicApp, timeit, Friend
from configparser import ConfigParser
import click
import os
import datetime
from ..initdb import Base, engine, db_session
from celery import Celery
from flask_socketio import SocketIO

# enviroment = 'ENV'

# import config from file
config = ConfigParser()
config.read('config.env')

Micro = Microservice(__name__)
print(config["ENV"]['CELERY_BROKER_URL'])
print(config["ENV"]['result_backend'])
Micro.app.config['CELERY_BROKER_URL'] = config["ENV"]['CELERY_BROKER_URL']
Micro.app.config['result_backend'] = config["ENV"]['result_backend']
socketio = SocketIO(Micro.app)
# socketio.namespace = "/deposit"
celery = Celery(Micro.app.name, backend=Micro.app.config['result_backend'], broker = Micro.app.config['CELERY_BROKER_URL'])
celery.conf.update(Micro.app.config)

@Micro.app.route('/')
def helloworld():
    return 'Hello World'


def init_db():
    """Initiate all database. This should be use one time only
    """
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from . import models
    Base.metadata.create_all(bind=engine)

# command line to start project

@click.command()
@click.option('--env', default='ENV', help='Setup enviroment variable.')
def main(env='ENV'):
    """Running method for Margin call app

    Keyword Arguments:
        env {str} -- Can choose between initdb, PROD, or ENV/nothing. 'initdb' will create database table and its structures, use onetime only .PROD only change debug variable in webapp to true (default: {'ENV'})
    """

    if env == 'initdb':
        init_db()
    else:
        env = str(env)
        debug = bool(config[env]['debug'] == 'True')
        print(debug)
        socketio.run(Micro.app,host=config[env]['host'], port=int(config[env]['port']),debug=True)
        # Micro.run(host=config[env]['host'], port=int(
        #     config[env]['port']), debug=True)
