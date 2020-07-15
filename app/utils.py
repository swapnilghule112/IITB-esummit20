from flask import render_template, flash, redirect, url_for, request, session,jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, ManufacturerForm, BrokerForm, SearchForm,Purchase_O , Sales_O, EndTrans
from app import app, mongo,db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.models import User
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from datetime import datetime
from werkzeug.http import HTTP_STATUS_CODES
from bson.objectid import ObjectId

import sys
import json


bdb_root_url = 'localhost:9984'

bdb = BigchainDB(bdb_root_url)

def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

def bad_request(error_str):
    response = jsonify({"error":str(error_str)})
    response.status_code = 404
    return response

# #buggy code starts here
def transfer_asset(username,serial_no,priv_key):
    results = bdb.assets.get(search = serial_no)
    try:
        if results:
            tx_results = bdb.transactions.get(asset_id = results[0]['id'])

            #if len(tx) is 1 then 1st transfer else subsequent
            if len(tx_results) == 1:
                creation_tx = tx_results[-1]
                asset_id = creation_tx['id']
                t = datetime.utcnow()
                transfer_asset = {
                        'id': asset_id,
                    }

                output_index = 0
                output = creation_tx['outputs'][output_index]
                transfer_input = {
                        'fulfillment': output['condition']['details'],
                        'fulfills': {
                            'output_index': output_index,
                            'transaction_id': creation_tx['id'],
                        },
                        'owners_before': output['public_keys'],
                    }
                broker = mongo.db.users.find_one({'username':username})
                pub_key_broker = broker['public_key']
                # manu = mongo.db.users.find_one({'username':username})
                priv_key_manu = priv_key
                prepared_transfer_tx = bdb.transactions.prepare(
                        operation='TRANSFER',
                        asset=transfer_asset,
                        inputs=transfer_input,
                        recipients=pub_key_broker,
                        metadata = {'timestamp': str(t)}
                )
                fulfilled_transfer_tx = bdb.transactions.fulfill(
                    prepared_transfer_tx,
                    private_keys = priv_key_manu,
                )
                
                commit_json = bdb.transactions.send_commit(fulfilled_transfer_tx)
                return commit_json
            else:
                # print(tx_results)
                # print(type(tx_results))
                transfer_tx = tx_results[-1]
                asset_id = transfer_tx['asset']['id']
                t = datetime.utcnow()
                transfer_asset = {
                        'id': asset_id,
                    }
                output_index = 0
                output = transfer_tx['outputs'][output_index]
                transfer_input = {
                        'fulfillment': output['condition']['details'],
                        'fulfills': {
                            'output_index': output_index,
                            'transaction_id': transfer_tx['id'],
                        },
                        'owners_before': output['public_keys'],
                        
                    }
                broker = mongo.db.users.find_one({'username':username})
                pub_key_broker = broker['public_key']
                manu = mongo.db.users.find_one({'username':username})
                priv_key_manu = priv_key
                prepared_transfer_tx = bdb.transactions.prepare(
                        operation='TRANSFER',
                        asset=transfer_asset,
                        inputs=transfer_input,
                        recipients=pub_key_broker,
                        metadata = {'timestamp': str(t)}
                )
                fulfilled_transfer_tx = bdb.transactions.fulfill(
                    prepared_transfer_tx,
                    private_keys = priv_key_manu,
                )
                print(fulfilled_transfer_tx)
                commit_json = bdb.transactions.send_commit(fulfilled_transfer_tx)
                return commit_json
    except Exception:
        strk = sys.exc_info()[0]
        flash("Something went wrong: "+str(strk))
        return None


            
#non buggy code starts here
def search_asset(serial_no):
    try:
        result = bdb.assets.get(search = serial_no)
        if result:
            creation_tx = bdb.transactions.get(asset_id = result[0]['id'])
            if creation_tx:		
                return creation_tx
            else:
                return {}
        else:
            flash("no results were found for this query")
    except Exception:
        exc_info = sys.exc_info()
        info = str(exc_info[0]) + " " + str(exc_info[2].tb_lineno)
        return bad_request(info)

def createasset(username,serial_no,cost,private_key):

    try:
        print("Into createasset")
        print(username)
        print(serial_no)
        print(cost)
        print(private_key)

        t = datetime.utcnow()
        sack = {
            'data': {
                'sack': {
                    'serial_number': serial_no,
                    'manufacturer': username,
                },
            },
        }
        metadata = {'cost': cost, 'timestamp': str(t)}

        try:
            users = mongo.db.users
            curr = users.find_one({'username': username})
            prepared_creation_tx = bdb.transactions.prepare(
                operation='CREATE',
                signers=curr['public_key'],
                asset=sack,
                metadata=metadata,
            )

            fulfilled_creation_tx = bdb.transactions.fulfill(
            prepared_creation_tx, private_keys=private_key)


            commit_json = bdb.transactions.send_async(fulfilled_creation_tx)
            print("commited successfully")
            print(commit_json)
            return commit_json
        except:
            strk = sys.exc_info()[0]
            print("error")
            print(strk)
            flash("Something went wrong: "+str(strk))
            return None
    
    except Exception:
        strm = sys.exc_info()[0]
        flash("Something went wrong: "+str(strm))
        print(strm)
        return None
