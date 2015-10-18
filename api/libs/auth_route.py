#!/usr/bin/env python

## @auth John Allard, Nick Church, others
## @date Oct 2015
## @github https://github.com/jhallard/praxyk
## @license MIT

## @info - This file defines all of the /users/ route for the Praxyk API.
##         This involved creating a class with the PUT, GET, POST, and 
##         DELETE methods defined. Once defined, the main API handler 
##         (../api_server.py) can simply import this class and use it to 
##         handle any user-related requests.

import sys, os
import argparse
import datetime
import json

from flask import Flask, jsonify, request, Response, g, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal, marshal_with
from flask.ext.httpauth import HTTPBasicAuth
from flask_jwt import JWT, jwt_required, current_identity

from flask.ext.security import (Security, SQLAlchemyUserDatastore, login_required, current_user,
                                roles_required, auth_token_required, UserMixin, RoleMixin)

from functools import wraps

from api import db, PRAXYK_API_APP
from api import User, Token, Role


# @info - decorator function, any function that this decorator is applied to will
#         have to have it's token argument validated with the auth util. All this
#         does is make sure the given token exists in the database and isn't expired.
def requires_auth(f):
    @wraps(f)                                                                                                                                        
    def decorated(*args, **kwargs):
        try :
            token = request.values.get('token')
            if not token:
                token = request.json.get('token')
    	    token = Token.query.filter_by(value="%s"%token).first_or_404()
            user = None if not token else token.user
            if not token or not user :
                return abort(403, "Token Could not Be Authenticated")
	        if not token.valid :
		        return abort(403, "Token has Expired")
            g._caller = user
            return f(*args, **kwargs)
        except Exception, e:
            print str(e)
            return abort(403)
    return decorated

# @info - called to make sure that the owner of a resource is the one trying to access
#         it, also allows root and admin users to access resource.
def validate_owner(caller, owner_id) :
    if caller.id == owner_id :
        return True
    roles = caller.roles
    for role in roles :
        if role == Role.ROLE_ROOT or role == ROLE_ADMIN :
            return True
    return False


# @info - class with routes that contain a user id 
# ie `GET api.praxyk.com/users/12345`
class AuthRoute(Resource) :

    def __init__(self) :
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email', type=str, required=True, location='json')
        self.reqparse.add_argument('password', type=str, required=True, location='json')
        super(AuthRoute, self).__init__()

    def post(self) :
        args = self.reqparse.parse_args()
        user = User.authenticate(args['email'], args['password'])

        if not user :
            abort(404)

        new_token = Token(user_id=user.id)

        if not new_token :
            abort(403)

        user.tokens.append(new_token)

        db.session.add(user)
        db.session.commit()
        return jsonify({"code" : 200, "user" : {"userid" : user.id, "email" : user.email}, "token" : new_token.value})

    @auth_token_required
    @roles_required('root')
    def delete(self, id) :
        pass
    




