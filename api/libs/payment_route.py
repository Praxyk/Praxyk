#!/usr/bin/env python

## @auth John Allard, Ryan Coley, others
## @date Oct 2015
## @github https://github.com/jhallard/praxyk
## @license MIT

## @info - This file defines all of the /payment/ route for the praxyk api. The user
## is able to add, remove, update and delete their payment information.

import sys, os
import argparse
import datetime
import json

from flask import Flask, jsonify, request, Response, g, abort, make_response, redirect, render_template, url_for
from flask.ext.restful import Api, Resource, reqparse, fields
from flask.ext.security import Security, SQLAlchemyUserDatastore

from api import db, PAYMENT_ENDPOINT,USER_ENDPOINT,USERS_ENDPOINT
from api import User, Role, user_datastore

from auth_route import *
from libs.route_fields import *

#stripe config
import stripe
from api.config import stripe_secret_key
stripe.api_key = stripe_secret_key


# @info - class that users can post/get from , in order to active their account that they previously registered.
class PaymentRoute(Resource) :

    def __init__(self) :
        self.reqparse = reqparse.RequestParser()
        super(PaymentRoute, self).__init__()
        
   #Add Payment info only if none on file
    @requires_auth
    def post(self, id) :
        try :
            caller = g._caller
            if not caller or not validate_owner(caller, id) :
                abort(404)
            
            user = User.query.get(id)
        
            if not user.payment_info.card_id == None :
               return jsonify({'code':400,'message':"There is already a card on file! Please delete that card to add another."})
               
            self.reqparse.add_argument('name', type=str, required=True, location='json')
            self.reqparse.add_argument('address1', type=str, required=True, location='json')
            self.reqparse.add_argument('address2', type=str, required=False, location='json')
            self.reqparse.add_argument('city', type=str, required=True, location='json')
            self.reqparse.add_argument('state', type=str, required=True, location='json')
            self.reqparse.add_argument('zip', type=int, required=True, location='json')
            self.reqparse.add_argument('card_number', type=int, required=True, location='json')
            self.reqparse.add_argument('exp_month', type=int, required=True, location='json')
            self.reqparse.add_argument('exp_year', type=int, required=True, location='json')
            self.reqparse.add_argument('cvc', type=str, required=True, location='json')
            args = self.reqparse.parse_args()
            
            token = stripe.Token.create(
               card={
                  "number":args.card_number,
                  "exp_month":args.exp_month,
                  "exp_year":args.exp_year,
                  "cvc":args.cvc,
                  "name":args.name,
                  "address_city":args.city,
                  "address_line1":args.address1,
                  "address_line2":args.address2,
                  "address_state":args.state,
                  "address_zip":args.zip
                  
               },)         
            customer = stripe.Customer.retrieve(user.payment_info.customer_id)
            card = customer.sources.create(source=token.id)
               
            user.payment_info.card_id = card.id
            user.active=True
               
            db.session.add(user)
            db.session.commit()
               
            return jsonify({'code':200,'message':'Your card was successfully added!'})
            
        except stripe.error.CardError, e:            
            return jsonify({'code': 400,'message':'There was an error with your card! Please make sure that all details are correct.'})
        except Exception, e:
            sys.stderr.write("Exception : " + str(e)+"\n")
            abort(404)
            
   #Retrieve Payment Info
    @requires_auth
    def get(self, id) :
        caller = g._caller
        if not caller or not validate_owner(caller, id) :
            abort(404)
	user = User.query.get(id)
	if user.payment_info.card_id == None:
		return jsonify({'code':400,'message':'You have no card on file!'})
	try:
            
         customer = stripe.Customer.retrieve(user.payment_info.customer_id)
         card = customer.sources.retrieve(user.payment_info.card_id)

         result = {
                  "code":200,
                  "message":"",
                  "number":card.last4,
                  "exp_month":card.exp_month,
                  "exp_year":card.exp_year,
                  "name":card.name,
                  "address1":card.address_line1,
                  "address2":card.address_line2,
                  "city":card.address_city,
                  "state":card.address_state,
                  "zip":card.address_zip,
                  "brand":card.brand
                  }
        
         return result
        
        except Exception, e:
            sys.stderr.write("Exception : " + str(e))
            abort(404)
        
    #Remove Payment Info
    @requires_auth
    def delete(self,id):
        caller = g._caller
        if not caller or not validate_owner(caller, id) :
            abort(404)
        user = User.query.get(id)
        try:
         if user.payment_info.card_id == None:
            return jsonify({'code':400,'message':"There is not a card on file!"})
            
         customer = stripe.Customer.retrieve(user.payment_info.customer_id)
         card = customer.sources.retrieve(user.payment_info.card_id).delete()
         
         if not card.deleted :
            return jsonify({'code':400,'message':"There was a problem removing your card!"})
            
         user.payment_info.card_id = None
         user.active=False
         
         db.session.add(user)
         db.session.commit()
        
         return jsonify({'code':200,'message':'Your card was successfully removed!'})
        
        except Exception, e:
            sys.stderr.write("Exception : " + str(e))
            abort(404)




