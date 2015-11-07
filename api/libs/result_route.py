#!/usr/bin/env python                                                                                                                                

## @auth John Allard, Nick Church, others
## @date Oct 2015
## @github https://github.com/jhallard/praxyk
## @license MIT

## Note - This model definition is shared across multiple servers and code branches, DO NOT
##        change this file unless you have permission or know exactly what you're doing. 


from flask.ext.restful import Api, Resource, reqparse, fields, marshal, inputs
from flask.ext.httpauth import HTTPBasicAuth
from flask import Flask, jsonify, request, Response, g, url_for

from api import db, USER_ENDPOINT, TRANSACTIONS_ENDPOINT, RESULTS_ENDPOINT
from api import *
from auth_route import *

from models.nosql.pod.result_pod_ocr import *
from models.nosql.result_base import *

from libs.route_fields import *
from libs.transactions_route import transaction_fields

DEFAULT_PAGE_SIZE = 100
DEFAULT_PAGE=1


# @info - this class defines the /results/<int:id> route, which allows user's to access all results for a
#         specific transaction given by @id. If a user wants to grab their results history across multiple
#         transactions, then can `GET /results/?user_id=<int:id>`
class ResultRoute(Resource):

    def __init__(self):
        self.transaction_id = None
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('pagination', type=inputs.boolean, default=True, location=['values', 'headers', 'json'])
        self.reqparse.add_argument('page', type=int, default=DEFAULT_PAGE, location=['values', 'json'])
        self.reqparse.add_argument('page_size', type=int, default=DEFAULT_PAGE_SIZE, location=['values', 'json'])
        super(ResultRoute, self).__init__()


    # @info - This handles all get requests for requests grouped under a specific transaction, aka this handles
    #         all requests of type `/results/:trans_id`. The results are paginated by default, this can be turned 
    #         of by giving ?pagination=False which will cause all results to be dumped in a single list.
    @requires_auth
    def get(self, id):
        try :
            caller = g._caller
            trans = Transaction.query.get(id)
            if not trans or not caller or not validate_owner(caller, trans.user_id) :
                abort(404)

            (service, model) = (trans.service, trans.model)
            results = {}

            if service == SERVICE_POD :
                if model == MODELS_POD_OCR :
                    results = self.get_results_pod_ocr(caller, trans)
                elif model == MODELS_POD_BAYES_SPAM :
                    results = {}
            elif service == SERVICE_TLP : 
                results = {}

            return jsonify(results)
        except Exception as e :
            print "Exception GET /results/X (%s)" % str(e)
            return abort(500)

    # @info - this function takes a transaction db model and returns the results associated with that
    #         request. This function makes use of the pagination scheme to return results, see the API
    #         docs for more info on pagination.
    def get_results_pod_ocr(self, caller, trans) :
        args = self.reqparse.parse_args()
        next_page_num = 0
        page = {}
        result_list = Result_POD_OCR.query.filter(transaction_id=trans.id).order_by('item_number').execute()

        if not result_list or len(result_list) != trans.uploads_success :
            print "\n\n Not All Result Recovered from Redis DB" + str(result_list) + "\n\n"

        if not args.pagination :
            results_json = []
            for res in result_list :
                results_json.append(marshal_result(res))
            return {"code" : 200, "transaction" : marshal(trans, transaction_fields), "results" : results_json } 

        page_results  = self.get_page_from_results(result_list, args.page, args.page_size)

        page_json = page_results.get('results_json', None)
        next_page_num = page_results.get('next_page_num', None)
        prev_page_num = page_results.get('prev_page_num', None)
        last_page_num = page_results.get('last_page_num', None)

        if page_json :
            page = {"page_number" : args.page, "results" : page_json}

        next_page = "" if not next_page_num else url_for(RESULT_ENDPOINT, id=trans.id,
                                                         page_size=args.page_size, page=next_page_num,
                                                         _external=True)
        prev_page = "" if not prev_page_num else url_for(RESULT_ENDPOINT, id=trans.id,
                                                         page_size=args.page_size, page=prev_page_num,
                                                         _external=True)
        first_page = url_for(RESULT_ENDPOINT, id=trans.id, page_size=args.page_size, page=1, _external=True)
        last_page = url_for(RESULT_ENDPOINT, id=trans.id, page_size=args.page_size, page=last_page_num, _external=True)



        return {"code"        : 200,
                "transaction" : marshal(trans, transaction_fields),
                "page"        : page,
                "next_page"   : next_page,
                "prev_page"   : prev_page,
                "first_page"  : first_page,
                "last_page"   : last_page} 
                

            
    # takes a list of results, a page number, and a page_size to find the index bounds
    # on the page and returns the page as a list of results
    # returns (result_list, next_page_num) where next_page_num is None if result_list contains
    # results of the last page
    def get_page_from_results(self, result_list, page, page_size) :
        startind = (page-1)*page_size
        endind = (page)*page_size-1
        amount = len(result_list)
        last_page_num = (amount/page_size) + 1

        if startind < 0 or startind > amount :
            return {'results_json' : None, 'next_page_num' : (None if endind >= len(result_list) else page+1),
                    'prev_page_num' : (None if page == 1 else page-1), 'last_page_num' : last_page_num}
        if endind < 0 :
            return {'results_json' : None, 'next_page_num' : (None if endind >= len(result_list) else page+1),
                    'prev_page_num' : (None if page == 1 else page-1), 'last_page_num' : last_page_num}

        results_json = []
        results_subset = result_list[startind:endind] if startind > 0 else result_list[:endind]
        # print str(results_subset) + "  " + str(result_list)
        for result in results_subset :
            results_json.append(marshal_result(result))

        res = {'results_json' : results_json,
               'next_page_num' : (None if endind >= len(result_list) else page+1),
               'prev_page_num' : (None if page == 1 else page-1),
               'last_page_num' : last_page_num}

        return res


