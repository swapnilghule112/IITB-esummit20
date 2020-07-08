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
            return commit_json
        except:
            strk = sys.exc_info()[0]
            flash("Something went wrong: "+str(strk))
            return None
    
    except Exception:
        strm = sys.exc_info()[0]
        flash("Something went wrong: "+str(strm))
        return None


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/index')
@login_required
def index():
    # return redirect(url_for('manufacturer'))
    user = session['username']
    fin = mongo.db.users.find_one({ 'username':user })
    flash('Pub: '+fin['public_key'])
    flash('Pri: '+fin['private_key'])
    s = ""
    for i in fin['owned']:
        s = s +", " + i
    flash('owned: '+s)
    role = fin['Role']
    return render_template('index.html', title='Home',user=user, role=role)



@app.route('/login', methods=['GET', 'POST'])
def login():
    role_ = ""
    form = LoginForm()
    if form.validate_on_submit():
        users = mongo.db.users
        login_u = users.find_one({'username':form.username.data})
        if login_u is None or not (check_password_hash(login_u['password_hash'],form.password.data)):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        role_= login_u['Role']
        # print(login_u)
        session["username"] = form.username.data
        log_in_user = User(login_u)
        # log_in_user.username = login_u["username"]
        login_user(log_in_user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        else:
            #return redirect(url_for('index'))
            return render_template('index.html', title='Sign In',role = "1",form=form)
        return redirect(next_page)         
    return render_template('login.html', title='Sign In',role = "1",form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        users = db.users
        existing_user = users.find_one({'username': form.username.data})

        if existing_user:
            flash('That username already exists..Try something else')
        else:
            user = generate_keypair()
            pub_key = user.public_key
            priv_key = user.private_key
            password_hash = generate_password_hash(form.password.data)
            mongo.db.users.insert({'username': form.username.data,'email': form.email.data,'Role':form.role.data, 'password_hash': password_hash, 'public_key': pub_key, 'private_key': priv_key, 'owned':[]})
            db.users.insert({'username': form.username.data,'email': form.email.data,'Role':form.role.data,'Org':form.org.data,'location':form.location.data,'details':form.details.data})
            # u = users.find_one({'username': form.username.data})
            # login_user(u)
            flash(f'Remember and keep your private key in a safe place {priv_key}')
            return redirect(url_for('index'))
    
    return render_template('register.html',title = 'Register', form =form)



@app.route('/manufacture',methods=['GET', 'POST'])
@login_required
def create_assets():
    form = ManufacturerForm()
    if form.validate_on_submit():
        serial_no = form.serialnumber.data
        ast_check = mongo.db.assets.find_one({'data.sack.serial_number':serial_no })
        if ast_check is not None:
            srn = str(serial_no)
            flash(srn+" is Already Taken Duplicate AssetID")
            return render_template('manufacturer.html', form = form)
        cost = form.cost.data
        private_key = form.private_key.data
        for i in range(1):
            create = createasset(session["username"],serial_no,cost,private_key)
        if create is not None:
            mongo.db.users.update_one({'username':session["username"] },{ '$addToSet': { 'owned':serial_no } } )
            flash("Asset created succesfully")
            return redirect(url_for('create_assets'))
    return render_template('manufacturer.html', form = form)



@app.route('/transaction', methods=['GET', 'POST'])
@login_required
def transaction():
    form = BrokerForm()
    if form.validate_on_submit():
        serial_no = form.serialnumber.data
        priv_key = form.private_key.data
        transact = transfer_asset(form.username.data,serial_no,priv_key)
        if transact is not None:
            mongo.db.users.update_one({'username':form.username.data },{ '$addToSet': { 'owned':serial_no } } )
            mongo.db.users.update_one({'username':session["username"] },{ '$pull': { 'owned':serial_no } } )
            flash('Transaction completed!!')
        else:
            flash('Transaction failed because asset was not found')
    fin = mongo.db.users.find_one({ 'username':session['username'] })
    role = fin['Role']
    return render_template('transaction.html', form = form, role = role)



@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    fin = mongo.db.users.find_one({ 'username':session['username'] })
    role = fin['Role']
    if form.validate_on_submit():
        serial_no = form.search.data
        result = search_asset(serial_no)
        if result is None:
            flash("not found")
        else:
            # flash(result)
            return render_template('result.html', result=result,role=role)
    return render_template('search.html', form = form,role=role)



@app.route('/purchase_order' , methods = ['GET', 'POST'])
@login_required
def purchase_order():
    usern = session['username']
    form = Purchase_O()
    if form.validate_on_submit():
        po = db.po
        po_rx = form.po_rx.data
        _id = po.insert({ 'po_sx': usern , 'po_rx': form.po_rx.data ,'quantity': form.quantity.data,'amount': form.amount.data , 'TC': form.TC.data, 'Status': 'Pending', 'assets': []})
        id = str(_id)
        flash('Purchase Order sent to '+ po_rx + ' with PO_ID: ' + id )
        return redirect(url_for('index'))
    return render_template('purc_ord.html', title='Purchase Order',form=form, usern=usern)

@app.route('/po_notify' , methods = ['GET', 'POST'])
@login_required
def po_notify():
    usern = session['username']
    pos_r = list(db.po.find({"po_rx": usern}))
    pos_s = list(db.po.find({"po_sx": usern}))
    return render_template('po_notify.html', title='Notification',pos_r=pos_r, pos_s =pos_s, usern=usern)

@app.route('/so_notify' , methods = ['GET', 'POST'])
@login_required
def so_notify():
    usern = session['username']
    sos_r = list(db.so.find({"so_rx": usern}))
    sos_s = list(db.so.find({"so_sx": usern}))
    return render_template('so_notify.html', title='Sales Notification',sos_r=sos_r , sos_s = sos_s, usern=usern)


@app.route('/sales' , methods = ['GET', 'POST'])
@login_required
def sales():
    if request.method == "POST":
        req = request.form
        id = req.get("po_id")
        return redirect(url_for('sales_order', po_id = id))
    return render_template('base.html')

@app.route('/end' , methods = ['GET', 'POST'])
@login_required
def end():
    if request.method == "POST":
        req = request.form
        id = req.get("so_id")
    
        return redirect(url_for('ends', so_id = id))
    return render_template('index.html')


@app.route('/cancel_so' , methods = ['GET', 'POST'])
@login_required
def cancel_so():
    if request.method == "POST":
        req = request.form
        id = req.get("so_id")
        db.so.update({'_id': ObjectId(id)}, {'$set':{'Status':'Cancelled'}})
        doc = db.so.find_one({'_id': ObjectId(id) }) 
        po_id = doc['po_id']
        db.po.update({'po_id': ObjectId(id)}, {'$set':{'Status':'Cancelled SO'}})
        flash('Sales order cancelled '+ id)
    return render_template('index.html')


@app.route('/cancel_po' , methods = ['GET', 'POST'])
@login_required
def cancel_po():
    if request.method == "POST":
        req = request.form
        id = req.get("po_id")
        db.po.update({'_id': ObjectId(id)}, {'$set':{'Status':'Cancelled'}})
        flash('Purchased order cancelled '+ id)
    return render_template('index.html')


@app.route('/sales_order' , methods = ['GET', 'POST'])
@login_required
def sales_order():
    po_id = request.args.get('po_id', None)
    doc = db.po.find_one({'_id': ObjectId(po_id)})
    usern = session['username']
    form = Sales_O()
    if form.validate_on_submit():
        so_rx= form.so_rx.data
        _id = db.so.insert({'po_id': po_id, 'so_sx': usern , 'so_rx': form.so_rx.data , 'org': form.org.data,'loc_ship': form.loc_ship.data , 'quant': form.quant.data, 'amount':form.amount.data , 'TC': form.TC.data, 'Status': 'Pending'})
        id = str(_id)
        db.po.update({'_id': ObjectId(po_id)}, {'$set':{'Status':'Accepted'}})
        flash('Sales Order placed to '+ so_rx + ' with SO_ID '+ id)
        return redirect(url_for('index'))
    return render_template('sales_ord.html', title = 'Sales order FORM', form =form, po_id = po_id, usern = usern)


@app.route('/ends' , methods = ['GET', 'POST'])
@login_required
def ends():
    so_id = request.args.get('so_id', None)
    doc = db.so.find_one({'_id': ObjectId(so_id)})
    usern = session['username']
    po_id = doc['po_id']
    db.po.update({'_id': ObjectId(po_id)}, {'$set':{'Status':'Completed'}})
    db.so.update({'_id': ObjectId(so_id)}, {'$set':{'Status':'Completed'}})
    flash('Transaction completed with PO_ID: '+ po_id+ ' and SO_ID: '+ so_id)
    return redirect(url_for('so_notify'))










# API routes starts from here

@app.route('/api/services/v1/getUserDetails', methods = ['POST'])
def get_user_details_api():
    response = jsonify({})
    response.status_code = 404
    try:
        #data = request.get_json() or {}
        data = json.loads(request.data)
        # user = mongo.db.users.find_one({'username':data['Data']['username']
        #data = {"Data": {"username": "preyash", "password": "12345"}}
        if (not ('username' in data['Data']) or not ('password' in data['Data'])):
            return bad_request('must include username and password fields')

        if not('username' in data["Data"]) or data["Data"]["username"] == "" or data["Data"]["username"] == None:
            return bad_request('enter valid username')
    

        if not('password' in data["Data"]) or data["Data"]["password"] == "" or data["Data"]["password"] == None:
            return bad_request('enter valid password')
    
        try:
            user = mongo.db.users.find_one({'username':data['Data']['username']})
        except Exception as e:
            print(e)

        if user is None:
            return bad_request('Username does not exist')

        if check_password_hash(user['password_hash'],data['Data']['password']) == False:
            return bad_request('Password not matching')
        else:
            user_obj = {}
            user_obj["username"] = user["username"]
            user_obj["email"] = user["email"]
            user_obj["role"] = user["Role"]
            user_obj["public_key"] = user["public_key"]
            user_obj["owned_assets"] = len(user["owned"])
            response = jsonify({'ReturnMsg':'Success','user':user_obj})
            response.status_code = 200
    except Exception as e:
        return bad_request(str(sys.exc_info()[0]) + " error on line no: " + str(sys.exc_info()[2].tb_lineno) + " Data received: " +  json.dumps(data))
    return response


@app.route('/api/services/v1/createAsset',methods = ['POST'])
def create_asset_api():
    app.logger.info("Inside create asset api")
    data = request.data
    data = json.loads(data)
    app.logger.info(data)
    if 'serial_no' not in data['Data'] or 'number_of_assets' not in data['Data'] or 'cost' not in data['Data'] or 'username' not in data['Data'] or 'private_key' not in data['Data']:
    #if False:
        return bad_request('One or more missing fields')
    
    response = createasset(data['Data']['username'],data['Data']['serial_no'], data['Data']['cost'],data['Data']['private_key'])
    app.logger.info("createasset response")
    app.logger.info(response)
    if response is None:
        return bad_request('Failed')
    
    response["ReturnMsg"] = "Success"
    response = jsonify(response)
    app.logger.info("Response")
    app.logger.info(response)
    response.status_code = 200
    return response

@app.route('/api/services/v1/transferAsset',methods = ['POST'])
def transfer_asset_api():
    app.logger.info("Into Transfer asset API ")
    data = request.data
    data = json.loads(data)
    app.logger.info("Request packet")
    app.logger.info(data)
    if 'serial_no' not in data['Data'] or 'number_of_assets' not in data['Data'] or 'public_key' not in data['Data'] or 'private_key' not in data['Data']:
        return bad_request('One or more missing fields')
    
    response = transfer_asset(data['Data']['username'],data['Data']['serial_no'],data['Data']['private_key'])
    
    if response is not None:
        response = jsonify(response)
        response.status_code = 200
    else:
        response = jsonify(response)
        response.status_code = 400
    return response

@app.route('/api/services/v1/search',methods = ['POST'])
def search_api():
    response = {}
    try:
        data = request.data
        data = json.loads(data)
        app.logger.info(data)
        serial_no = data["Data"]["serial_no"]
        response = search_asset(serial_no)
        response = jsonify(response)
        response.status_code = 200
        return response
    except:
        exc_info = sys.exc_info()
        return bad_request(str(exc_info[0]) + " " + str(exc_info[2].tb_lineno) + json.dumps(data))

@app.route('/api/services/v1/getCurrentOwnedAssets',methods = ['POST'])
def get_current_owned_assets():
    response = bdb.outputs.get('7gu4F9eUNAWG5y1Dc61mis3JSWHqayEVnHYNrjzSjHYL', spent = True)

    r = bdb.outputs.get('7gu4F9eUNAWG5y1Dc61mis3JSWHqayEVnHYNrjzSjHYL', spent = False)
    
    set1 = set([i['transaction_id'] for i in response])

    set2 = set([i["transaction_id"] for i in r])

    # print(set1)
    # print(set2)
    # print()
    # print()
    # res = set1.intersection(set2)

    # print(len(set1)- len(set2))
    response[0]["no_of_assets"] = len(set2)- len(set1)
    return jsonify(response)

@app.route('/api/services/v1/getTrackingInfo', methods = ['POST'])
def get_tracking_info_api():
    return {}

@app.route('/api/services/v1/getUserInfo', methods = ['POST'])
def get_user_info():
    return {}

@app.route('/api/services/v1/getAnalyticsInfo', methods = ['POST'])
def get_analytics_info():
    return {}
