#!/usr/bin/env python

## @auth John Allard, Nick Church, others
## @date Oct 2015
## @github https://github.com/jhallard/praxyk
## @license MIT

########################################################################################
#                                  Praxyk API Server                                   #
#  This is the main request handling code for the user-facing API server. It defines   #
#  exactly how to respond to all of the valid route requests that we recieve from      #
#  users. It depends on a series of util classes defined in /libs/, these abstract the #
#  process of authentication and user-data distribution out from the actual request    #
#  handling code.                                                                      #
#                                     Arguments                                        #
#  Use -h or --help to print script help                                               #
#                                                                                      #
#  See https://github.com/jhallard/Praxyk/wiki/Praxyk-API for complete API guide.      #
########################################################################################

import sys, os
import argparse
import datetime
import json

# routes includes
from libs.users_route import UserRoute, UsersRoute, user_fields
from libs.transactions_route import TransactionRoute, TransactionsRoute
from libs.results_route import ResultsRoute
from libs.result_route import ResultRoute
from libs.auth_route import AuthRoute
from libs.confirm_route import ConfirmRoute
from libs.pod.pod_route import POD_Route
from libs.pod.ocr_route import POD_OCR_Route
from libs.pod.bayes_spam_route import POD_Bayes_Spam_Route

# queue includes
from queue.task_lib import *
from queue.start_worker import *

# model includes
from models import *

#flask includes
from flask import Flask, jsonify, request, Response, g
from flask import Flask, jsonify, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask.ext.httpauth import HTTPBasicAuth

from functools import wraps

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from api import * # imports all defines from top-level __init__


DESCRIPTION = """

"""

# @info - parse command line args into useable dictionary
#         right now we only take a config file as an argument
def parse_args(argv) :
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--port',  default=5000, help="This is the port the server will be run locally on. Defualt is 5000")
    parser.add_argument('--builddb', action='store_true', help="This will cause all of the tables to be dropped and remade.")
    parser.add_argument('--local', action='store_true', help="Use this flag to run the server on " + \
                                                             "localhost:5000 instead of $IPADDR:5000.")
    return parser.parse_args()


# @info - start adding the API endpoints. Each endpoint gets its own class. 
#         The classes are in /praxyk/api/libs/*_route.py
#	      All of the constants are defined in /api/__init__.py
api.add_resource(AuthRoute, TOKENS_ROUTE, endpoint=TOKEN_ENDPOINT)
api.add_resource(AuthRoute, AUTH_ROUTE, endpoint=AUTH_ENDPOINT)
api.add_resource(AuthRoute, LOGIN_ROUTE, endpoint=LOGIN_ENDPOINT)

api.add_resource(UserRoute, USER_ROUTE, endpoint=USER_ENDPOINT)
api.add_resource(UsersRoute, USERS_ROUTE, endpoint=USERS_ENDPOINT)

api.add_resource(TransactionsRoute, TRANSACTIONS_ROUTE, endpoint=TRANSACTIONS_ENDPOINT)
api.add_resource(TransactionRoute, TRANSACTION_ROUTE, endpoint=TRANSACTION_ENDPOINT)

api.add_resource(ResultsRoute, RESULTS_ROUTE, endpoint=RESULTS_ENDPOINT)
api.add_resource(ResultRoute, RESULT_ROUTE, endpoint=RESULT_ENDPOINT)

api.add_resource(ConfirmRoute, CONFIRM_ROUTE, endpoint=CONFIRM_ENDPOINT)

api.add_resource(POD_Route, POD_ROUTE, endpoint=POD_ENDPOINT)
api.add_resource(POD_OCR_Route, POD_OCR_ROUTE, endpoint=POD_OCR_ENDPOINT)
api.add_resource(POD_Bayes_Spam_Route, POD_BAYES_SPAM_ROUTE, endpoint=POD_BAYES_SPAM_ENDPOINT)

@PRAXYK_API_APP.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


def create_initial_users() :
    with PRAXYK_API_APP.app_context():
        for name in Role.rolenames :
            db.session.add(Role(name=name))
        db.session.commit()

        for user in INITIAL_USERS:
            new_user = user_datastore.create_user(name=user['name'], email=user['email'], password=user['password'], active=True)
            user_datastore.activate_user(new_user)
            role = user_datastore.find_role(user['role'])
            user_datastore.add_role_to_user(new_user, role)
            db.session.commit()

# @info - Main function, parse the inputs to see if the database needs to be either build or created
#         if so, build, fill and exit. IF not, then just run in a infinite loop waiting for requests to 
#         handle
if __name__ == '__main__':
    
    args = parse_args(sys.argv)
    # @info - you can do stuff here before the app actually starts running, like setup db connections
    #         or make sure other servers are active, etc.
    with PRAXYK_API_APP.app_context():
        if args.builddb :
            db.drop_all()
            db.create_all()
            create_initial_users()
            sys.exit(0)	

    # will run on localhost:5000 if --local flag is given
    if args.local :
        PRAXYK_API_APP.run(port=int(args.port), debug=True, threaded=True)
    # else we run a http server that can listen for foreign connections on port 5000
    else :
        http_server = HTTPServer(WSGIContainer(PRAXYK_API_APP))
        http_server.listen(int(args.port))
        IOLoop.instance().start()



