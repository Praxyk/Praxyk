#!/usr/bin/env python                                                                                                                                

## @auth John Allard, Nick Church, others
## @date Oct 2015
## @github https://github.com/jhallard/praxyk
## @license MIT
import sys

from flask import Flask, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request, Response, g, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask.ext.bcrypt import Bcrypt
from flask.ext.cors import CORS
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, roles_required
from flask_mail import Mail
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
# from flask.ext.rq import RQ

import redis
from config import apiconf, REDIS_CONF, stripeconf

sys.path.append('../')

from models import *
from queue import *


PRAXYK_API_APP = Flask(__name__) # our main flask app object
PRAXYK_API_APP.config.from_object('api.config') # our main flask app object configured from 'config.py'

# security and auth default args
PRAXYK_API_APP.config['SECURITY_TOKEN_AUTHENTICATION_KEY'] = 'token'
PRAXYK_API_APP.config['SECURITY_PASSWORD_HASH'] = apiconf['security_password_hash']
PRAXYK_API_APP.config['SECURITY_PASSWORD_SALT'] = apiconf['security_password_salt']
PRAXYK_API_APP.config['WTF_CSRF_ENABLED'] = False

INITIAL_USERS = apiconf['users'] # list of initial users (root, admins, etc) to add to database upon creation

api = Api(PRAXYK_API_APP)        # our flask.restful api object that we use for routing
db = SQLAlchemy(PRAXYK_API_APP)  # this is our handle to the database
bcrypt = Bcrypt(PRAXYK_API_APP)  # used for password hashing
CORS(PRAXYK_API_APP)             # cross-site scripting
# RQ(PRAXYK_API_APP)               # redis queue

BASE_URL           = "localhost"
VERSION            = "/v1"

# routes
LOGIN_ROUTE        = VERSION + "/login/"
TOKENS_ROUTE       = VERSION + "/tokens/"
AUTH_ROUTE         = VERSION + "/auth/"
TRANSACTIONS_ROUTE = VERSION + "/transactions/"
USERS_ROUTE        = VERSION + "/users/"
RESULTS_ROUTE      = VERSION + "/results/"
CONFIRM_ROUTE      = VERSION + "/confirm/<string:id>"
POD_ROUTE          = VERSION + "/pod/"
RESULTS_ROUTE      = VERSION + '/results/'
RESULT_ROUTE       = RESULTS_ROUTE + '<int:id>'
TRANSACTION_ROUTE  = TRANSACTIONS_ROUTE + '<int:id>'
USER_ROUTE         = USERS_ROUTE + '<int:id>'
POD_OCR_ROUTE        = POD_ROUTE + "ocr/"
POD_FACE_DETECT_ROUTE = POD_ROUTE + "face_detect/"
POD_BAYES_SPAM_ROUTE = POD_ROUTE + "bayes_spam/"
PAYMENT_ROUTE        = VERSION + "/payment/<int:id>"
PAYMENT_HANDLER_ROUTE = VERSION + "/payment_handler/<string:webhook>"
COUPON_ROUTE        = VERSION + "/coupon/<int:id>"

# endpoints
TRANSACTIONS_ENDPOINT = 'transactions'
TRANSACTION_ENDPOINT  = 'transaction'
USER_ENDPOINT         = 'user'
USERS_ENDPOINT        = 'users'
RESULTS_ENDPOINT      = 'results'
RESULT_ENDPOINT       = 'result'
TOKEN_ENDPOINT        = 'tokens'
AUTH_ENDPOINT         = 'auth'
LOGIN_ENDPOINT        = 'login'
CONFIRM_ENDPOINT      = 'confirm'
POD_ENDPOINT             = "pod"
POD_OCR_ENDPOINT         = POD_ENDPOINT + "_ocr"
POD_FACE_DETECT_ENDPOINT = POD_ENDPOINT + "_face_detect"
POD_BAYES_SPAM_ENDPOINT  = POD_ENDPOINT + "_bayes_spam"
PAYMENT_HANDLER_ENDPOINT = 'payment_handler'
PAYMENT_ENDPOINT = 'payment'
COUPON_ENDPOINT = 'coupon'

# services
SERVICE_POD = "pod"
SERVICE_TLP = "tlp"
SERVICES = [SERVICE_POD, SERVICE_TLP]

# models
MODELS_POD_OCR = "ocr"
MODELS_POD_BAYES_SPAM = "bayes_spam"
MODELS_POD_FACE_DETECT = "face_detect"
MODELS = [MODELS_POD_OCR, MODELS_POD_BAYES_SPAM, MODELS_POD_FACE_DETECT]


# mail settings
PRAXYK_API_APP.config['MAIL_SERVER']   = 'smtp.googlemail.com'
PRAXYK_API_APP.config['MAIL_PORT']     = 587
PRAXYK_API_APP.config['MAIL_USE_TLS']  = True
PRAXYK_API_APP.config['MAIL_USE_SSL']  = False
# gmail authentication
PRAXYK_API_APP.config['MAIL_USERNAME'] = apiconf['email']
PRAXYK_API_APP.config['MAIL_PASSWORD'] = apiconf['emailpassword']

mail = Mail(PRAXYK_API_APP)

# mail accounts
PRAXYK_API_APP.config['MAIL_DEFAULT_SENDER'] = 'from@example.com'

# default access token expiration time (24 hours)
TOKEN_EXPIRATION = apiconf['token_expiration']


from models.sql.user import User, Role, Transaction, Token, Payment_Info

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(PRAXYK_API_APP, user_datastore)
# PRAXYK_API_APP.config['SECURITY_CONFIRMABLE']

# Redis config for the queueing system
redis_host = REDIS_CONF.get('dbip', "")
redis_port = REDIS_CONF.get('port', "")
redis_pw   = REDIS_CONF.get('dbpasswd', "")
redis_num  = REDIS_CONF.get('dbnum', "")
# redis      = redis.Redis(host=redis_host, port=redis_port, password=redis_pw)
redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port, password=redis_pw, db=redis_num)



