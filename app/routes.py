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
import bson

import requests
import copy
from .utils import *
from .tasks import *
import jinja2
from xhtml2pdf import pisa


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
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        app.logger.error(str(e) + "on line no: " + str(exc_tb.tb_lineno))
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
@app.route('/index')
@login_required
def index():
    # return redirect(url_for('manufacturer'))
    user = session['username']
    fin = mongo.db.users.find_one({ 'username':user })
    own = db.users.find_one({ 'username':user })
    flash('Pub: '+fin['public_key'])
    flash('Pri: '+fin['private_key'])
    s = ""
    for i in own['owned']:
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
            mongo.db.users.insert({'username': form.username.data,'email': form.email.data,'Role':form.role.data, 'password_hash': password_hash, 'public_key': pub_key, 'private_key': priv_key})
            db.users.insert({'username': form.username.data,'email': form.email.data,'Role':form.role.data,'Org':form.org.data,'location':form.location.data,'details':form.details.data, 'owned':[], 'lock':[]})
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
            db.users.update_one({'username':session["username"] },{ '$addToSet': { 'owned':serial_no } } )
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
            db.users.update_one({'username':form.username.data },{ '$addToSet': { 'owned':serial_no } } )
            db.users.update_one({'username':session["username"] },{ '$pull': { 'owned':serial_no } } )
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
        _id = po.insert({ 'po_sx': usern , 'po_rx': form.po_rx.data ,'prod_name': form.prod_name.data ,'quantity': form.quantity.data,'amount': form.amount.data , 'TC': form.TC.data, 'Status': 'Pending', 'assets': []})
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
    usern = session['username']
    if request.method == "POST":
        req = request.form
        id = req.get("po_id")
        own = db.users.find_one({ 'username': usern })
        amount = db.po.find_one({'_id': ObjectId(id)})
        owned = len(own['owned'])
        quantity = int(amount['quantity'])
        if(owned < quantity):
            flash("You have less Assets, Cannot Complete your Order")
            return redirect(url_for('index'))
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
    qunt = int(doc['quantity'])
    usern = session['username']
    own = db.users.find_one({ 'username': usern })
    own = own['owned']
    ownt = own
    form = Sales_O()
    poid = []
    if form.validate_on_submit():
        so_rx= form.so_rx.data
        _id = db.so.insert({'po_id': po_id, 'so_sx': usern , 'so_rx': form.so_rx.data , 'org': form.org.data,'loc_ship': form.loc_ship.data , 'quant': form.quant.data, 'amount':form.amount.data , 'TC': form.TC.data, 'Status': 'Pending'})
        id = str(_id)
        db.po.update({'_id': ObjectId(po_id)}, {'$set':{'Status':'Accepted'}})
        for i in range(0,qunt):
            poid.append(own[i])
            ownt.remove(own[i])
        db.users.update({ "username" : usern}, { "$set": {'owned': ownt}})
        data = {po_id:poid}
        db.users.update_one({'username':usern },{ '$push': { 'lock': data } } )
        db.po.update({'_id': ObjectId(po_id)}, {'$set':{'assets': poid}})
        flash('Sales Order placed to '+ so_rx + ' with SO_ID '+ id)
        return redirect(url_for('index'))
    return render_template('sales_ord.html', title = 'Sales order FORM', form =form, po_id = po_id, usern = usern)

def get_priv_key_by_username(username):
    urls = ["http://35.172.121.202/api/services/v1/get_priv_key","http://3.92.96.170/api/services/v1/get_priv_key","http://3.215.183.155/api/services/v1/get_priv_key"]
    data = {"username":username}
    print("Inside get_priv_key fun")
    data = json.dumps(data)
    print(data)
    for url in urls:
        api_resp = requests.post(url,data)
        print(api_resp)
        print(type(api_resp.text))
        api_resp = json.loads(api_resp.text)
        if "priv_key" in api_resp:
            return api_resp["priv_key"]
    else:
        return None

@app.route('/ends' , methods = ['GET', 'POST'])
@login_required
def ends():
    so_id = request.args.get('so_id', None)
    doc = db.so.find_one({'_id': ObjectId(so_id)})
    usern = session['username']
    po_id = doc['po_id']
    assets = db.po.find_one({'_id': ObjectId(po_id)})
    assets = assets['assets']
    so_sx = doc['so_sx']
    
    priv_key = get_priv_key_by_username(so_sx)
    if priv_key is None:
        flash("User not found")
        return redirect(url_for('index'))
    transferred = transfer_asset_async(usern,'random',priv_key,len(assets),assets)
    lock = db.users.find_one({"username": so_sx})
    lock = lock["lock"]
    for i in range(0,len(lock)):
        if po_id in lock[i]:
            lock.pop(i)
            break
    ast = db.users.find_one({"username":usern})
    ast = ast["owned"]
    assets.extend(ast)
    db.users.update({"username":so_sx},{'$set':{'lock':lock}})
    db.users.update({"username":usern},{"$set": {'owned': assets }})
    db.po.update({'_id': ObjectId(po_id)}, {'$set':{'Status':'Completed'}})
    db.so.update({'_id': ObjectId(so_id)}, {'$set':{'Status':'Completed'}})
    flash('Transaction completed with PO_ID: '+ po_id+ ' and SO_ID: '+ so_id)
    return redirect(url_for('so_notify'))










# API routes starts from here

@app.route('/api/services/v1/get_po_invoice', methods = ['POST'])
def get_po_invoice():
    response = jsonify({})
    response.status_code = 404
    try:
        app.logger.info(request)
        data = json.loads(request.data)
        if (not ('username' in data['Data']) or not ('po_id' in data['Data'])):
            bad_request('Content Incomplete')
        templateLoader = jinja2.FileSystemLoader(searchpath="/home/ubuntu/SIH-2020/app/templates")
        templateEnv = jinja2.Environment(loader=templateLoader)
        app.logger.info("reached po invoice 1")
        TEMPLATE_FILE = "recipt.html"
        template = templateEnv.get_template(TEMPLATE_FILE)
        content = db.po.find_one({'_id':ObjectId(data['Data']['po_id'])})
        user = db.users.find_one({'username':content['po_sx']})
        ids = "po_"+data['Data']['po_id']+".pdf"
        app.logger.info(ids)
        sourceHtml = template.render(content=content, user=user, io="Purchase Order")
        resultFile = open('/home/ubuntu/SIH-2020/app/static/po/'+ids, "w+b")
        pisaStatus = pisa.CreatePDF(sourceHtml,dest=resultFile)
        resultFile.close()
        url = 'http://3.92.96.170/static/po/'+ids
        app.logger.info(url)
        response = jsonify({'ReturnMsg':'Success','url':url})
        response.status_code = 200
    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        logger.error(str(e) + "on line no: " + exc_tb.tb_lineno)
        return bad_request(str(sys.exc_info()[0]) + " error on line no: " + str(sys.exc_info()[2].tb_lineno) + " Data received: " +  json.dumps(data))
    return response

@app.route('/api/services/v1/get_so_invoice', methods = ['POST'])
def get_so_invoice():
    response = jsonify({})
    response.status_code = 404
    try:
        app.logger.info(request)
        data = json.loads(request.data)
        if (not ('username' in data['Data']) or not ('so_id' in data['Data'])):
            bad_request('Content Incomplete')
        templateLoader = jinja2.FileSystemLoader(searchpath="/home/ubuntu/SIH-2020/app/templates")
        templateEnv = jinja2.Environment(loader=templateLoader)
        app.logger.info("reached so invoice 1")
        TEMPLATE_FILE = "recipt.html"
        template = templateEnv.get_template(TEMPLATE_FILE)
        cont = db.so.find_one({'_id':ObjectId(data['Data']['so_id'])})
        content = db.po.find_one({'_id':ObjectId(cont['po_id'])})
        user = db.users.find_one({'username':cont['so_sx']})
        ids = "so_"+data['Data']['so_id']+".pdf"
        app.logger.info(ids)
        sourceHtml = template.render(content=content, user=user, io="Sales Order")
        resultFile = open('/home/ubuntu/SIH-2020/app/static/so/'+ids, "w+b")
        pisaStatus = pisa.CreatePDF(sourceHtml,dest=resultFile)
        resultFile.close()
        url = 'http://3.92.96.170/static/so/'+ids
        app.logger.info(url)
        response = jsonify({'ReturnMsg':'Success','url':url})
        response.status_code = 200
    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        logger.error(str(e) + "on line no: " + exc_tb.tb_lineno)
        return bad_request(str(sys.exc_info()[0]) + " error on line no: " + str(sys.exc_info()[2].tb_lineno) + " Data received: " +  json.dumps(data))
    return response




@app.route('/api/services/v1/order_finalize', methods = ['POST'])
def order_finalize():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data']) or not ('so_id' in data['Data'])):
            return bad_request('Content Incomplete Not Found')
        so_id = data['Data']['so_id']
        doc = db.so.find_one({'_id': ObjectId(so_id)})
        usern = data['Data']['username']
        po_id = doc['po_id']
        assets = db.po.find_one({'_id': ObjectId(po_id)})
        assets = assets['assets']
        so_sx = doc['so_sx']
        priv_key = get_priv_key_by_username(so_sx)
        if priv_key is None:
            return bad_request("User not found")
        transferred = transfer_asset_async(usern,'random',priv_key,len(assets),assets)
        lock = db.users.find_one({"username": so_sx})
        lock = lock["lock"]
        for i in range(0,len(lock)):
            if po_id in lock[i]:
                lock.pop(i)
                break
        ast = db.users.find_one({"username":usern})
        ast = ast["owned"]
        assets.extend(ast)
        db.users.update({"username":so_sx},{'$set':{'lock':lock}})
        db.users.update({"username":usern},{"$set": {'owned': assets }})
        db.po.update({'_id': ObjectId(po_id)}, {'$set':{'Status':'Completed'}})
        db.so.update({'_id': ObjectId(so_id)}, {'$set':{'Status':'Completed'}})
        user_obj = {}
        user_obj["po_id"] = po_id
        user_obj["so_id"] = so_id
        response = jsonify({'ReturnMsg':'Success','user':user_obj})
        response.status_code = 200
    except Exception as e:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        logger.error(str(e) + "on line no: " + exc_tb.tb_lineno)
        return bad_request(str(sys.exc_info()[0]) + " error on line no: " + str(sys.exc_info()[2].tb_lineno) + " Data received: " +  json.dumps(data))
    return response


@app.route('/api/services/v1/get_sales_order', methods = ['POST'])
def get_sales_order():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data'])  or not ('po_id' in data['Data'])  or not ('so_rx' in data['Data']) or not ('org' in data['Data']) or not ('loc_ship' in data['Data']) or not ('TC' in data['Data'])):
            return bad_request('Content Incomplete Not Found')
        usern = data['Data']['username']
        existing_user = db.users.find_one({'username': data['Data']['so_rx']})
        if existing_user:
            so_rx = data['Data']['so_rx']
            po_id = data['Data']['po_id']
            pos = db.po.find_one({'_id':ObjectId(po_id)})
            quant = pos['quantity']
            amount = pos['amount']
            own = db.users.find_one({ 'username': usern })
            own = own['owned']
            ownt = own
            poid = []
            date = str(datetime.utcnow())
            _id =  db.so.insert({ 'po_id': po_id ,'so_sx': usern ,'so_rx': so_rx , 'org':data['Data']['org'] , 'loc_ship':data['Data']['loc_ship'] , 'quant': quant , 'amount': amount , 'TC': data['Data']['TC'], 'Status':'Pending', 'Date':date })
            _id = str(_id)
            db.po.update({'_id': ObjectId(po_id)}, {'$set':{'Status':'Accepted'}})
            for i in range(0,int(quant)):
                poid.append(own[i])
                ownt.remove(own[i])
            db.users.update({ "username" : usern}, { "$set": {'owned': ownt}})
            data = {po_id:poid}
            db.users.update_one({'username':usern },{ '$push': { 'lock': data } } )
            db.po.update({'_id': ObjectId(po_id)}, {'$set':{'assets': poid}})
            response = jsonify({'ReturnMsg':'Success','id':_id})
            response.status_code = 200
        else:
            return bad_request("Username Not Found")
    except Exception as e:
        print(e)
    return response

def rollback_ast(po_id):
    rolb = db.po.find_one({'_id': ObjectId(po_id)})
    assets = rolb['assets']
    ast = db.users.find_one({"username":rolb['po_rx']})
    ast = ast["owned"]
    assets.extend(ast)
    db.users.update({"username":rolb['po_rx']},{"$set": {'owned': assets }})
    return True


@app.route('/api/services/v1/so_cancel', methods = ['POST'])
def so_cancel():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('so_id' in data['Data'])):
            return bad_request('Sales Order Not Found')
        id = data['Data']['so_id']
        db.so.update({'_id': ObjectId(id)}, {'$set':{'Status':'Cancelled'}})
        doc = db.so.find_one({'_id': ObjectId(id) }) 
        po_id = doc['po_id']
        rol = rollback_ast(po_id)
        db.po.update({'po_id': ObjectId(id)}, {'$set':{'Status':'Cancelled SO'}})
        response = jsonify({'ReturnMsg':'Success','Status':'Sales order cancelled'})
        response.status_code = 200
    except Exception as e:
        print(e)
    return response




@app.route('/api/services/v1/get_purchase_order', methods = ['POST'])
def get_purchase_order():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data']) or not ('po_rx' in data['Data']) or not ('prod_name' in data['Data']) or not ('quantity' in data['Data']) or not ('amount' in data['Data']) or not ('TC' in data['Data'])):
            return bad_request('Content Incomplete Not Found')
        usern = data['Data']['username']
        existing_user = db.users.find_one({'username': data['Data']['po_rx']})
        if existing_user:
            po = db.po
            po_rx = data['Data']['po_rx']
            date = str(datetime.utcnow())
            _id =  po.insert({ 'po_sx': usern , 'po_rx': po_rx ,'prod_name': data['Data']['prod_name'] ,'quantity': data['Data']['quantity'], 'amount': data['Data']['amount'], 'TC': data['Data']['TC'], 'Status':'Pending', 'Date':date,'assets':[]})
            _id = str(_id)
            response = jsonify({'ReturnMsg':'Success','id':_id})
            response.status_code = 200
        else:
            return bad_request("Username Not Found")
    except Exception as e:
        print(e)
    return response


@app.route('/api/services/v1/po_cancel', methods = ['POST'])
def po_cancel():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('po_id' in data['Data'])):
            return bad_request('Purchase Order Not Found')
        id = data['Data']['po_id']
        db.po.update({'_id': ObjectId(id)}, {'$set':{'Status':'Cancelled'}})
        response = jsonify({'ReturnMsg':'Success','Status':'Purchased order cancelled'})
        response.status_code = 200
    except Exception as e:
        print(e)
    return response



@app.route('/api/services/v1/po_accept', methods = ['POST'])
def po_accept():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('po_id' in data['Data'])):
            return bad_request('Content PO ID Not Found')
        id = data['Data']['po_id']
        amount = db.po.find_one({'_id': ObjectId(id)})
        usern = amount['po_rx']
        own = db.users.find_one({ 'username': usern })
        owned = len(own['owned'])
        quantity = int(amount['quantity'])
        if(owned < quantity):
            response = jsonify({'ReturnMsg':'Success','Status':'false'})
            response.status_code = 200
            return response
        response = jsonify({'ReturnMsg':'Success','Status':'true'})
        response.status_code = 200
    except Exception as e:
        print(e)
    return response




@app.route('/api/services/v1/po_notify_r', methods = ['POST'])
def get_po_notify_r():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data'])):
            return bad_request('Username Not Found')
        usern = data['Data']['username']
        pos_r = db.po.find({"po_rx": usern})
        #pos_s = list(db.po.find({"po_sx": usern}))
        user_obj = {user_obj: {} for user_obj in range(pos_r.count())} #Creating Empty Nested Dic
        for k in range(0,pos_r.count()):   #Inserting Values into that Dic
            id = str(pos_r[k]["_id"])
            user_obj[k]["po_id"] = id
            user_obj[k]["po_sx"] = pos_r[k]["po_sx"]
            user_obj[k]["po_rx"] = pos_r[k]["po_rx"]
            user_obj[k]["quantity"] = pos_r[k]["quantity"]
            user_obj[k]["amount"] = pos_r[k]["amount"]
            user_obj[k]["TC"] = pos_r[k]["TC"]
            user_obj[k]["Status"] = pos_r[k]["Status"]
            user_obj[k]["assets"] = pos_r[k]["assets"]
            user_obj[k]["Date"] = pos_r[k]["Date"]
        response = jsonify({'ReturnMsg':'Success','user':user_obj}) 
        response.status_code = 200
    except Exception as e:
        print(e)
    return response



@app.route('/api/services/v1/po_notify_s', methods = ['POST'])
def get_po_notify_s():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data'])):
            return bad_request('Username Not Found')
        usern = data['Data']['username']
        pos_r = db.po.find({"po_sx": usern})
        user_obj = {user_obj: {} for user_obj in range(pos_r.count())} #Creating Empty Nested Dic
        for k in range(0,pos_r.count()):   #Inserting Values into that Dic
            id = str(pos_r[k]["_id"])
            user_obj[k]["po_id"] = id
            user_obj[k]["po_sx"] = pos_r[k]["po_sx"]
            user_obj[k]["po_rx"] = pos_r[k]["po_rx"]
            user_obj[k]["quantity"] = pos_r[k]["quantity"]
            user_obj[k]["amount"] = pos_r[k]["amount"]
            user_obj[k]["TC"] = pos_r[k]["TC"]
            user_obj[k]["Status"] = pos_r[k]["Status"]
            user_obj[k]["assets"] = pos_r[k]["assets"]
            user_obj[k]["Date"] = pos_r[k]["Date"]
        response = jsonify({'ReturnMsg':'Success','user':user_obj}) 
        response.status_code = 200
    except Exception as e:
        print(e)
    return response




@app.route('/api/services/v1/so_notify_s', methods = ['POST'])
def get_so_notify_s():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data'])):
            return bad_request('Username Not Found')
        usern = data['Data']['username']
        pos_s = db.so.find({"so_sx": usern})
        user_obj = {user_obj: {} for user_obj in range(pos_s.count())} #Creating Empty Nested Dic
        for k in range(0,pos_s.count()):   #Inserting Values into that Dic
            id = str(pos_s[k]["_id"])
            user_obj[k]["so_id"] = id
            user_obj[k]["po_id"] = pos_s[k]["po_id"]
            user_obj[k]["so_sx"] = pos_s[k]["so_sx"]
            user_obj[k]["so_rx"] = pos_s[k]["so_rx"]
            user_obj[k]["org"] = pos_s[k]["org"]
            user_obj[k]["loc_ship"] = pos_s[k]["loc_ship"]
            user_obj[k]["quant"] = pos_s[k]["quant"]
            user_obj[k]["amount"] = pos_s[k]["amount"]
            user_obj[k]["TC"] = pos_s[k]["TC"]
            user_obj[k]["Status"] = pos_s[k]["Status"]
            user_obj[k]["Date"] = pos_s[k]["Date"]
        response = jsonify({'ReturnMsg':'Success','user':user_obj}) 
        response.status_code = 200
    except Exception as e:
        print(e)
    return response



@app.route('/api/services/v1/so_notify_r', methods = ['POST'])
def get_so_notify_r():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (not ('username' in data['Data'])):
            return bad_request('Username Not Found')
        usern = data['Data']['username']
        pos_s = db.so.find({"so_rx": usern})
        user_obj = {user_obj: {} for user_obj in range(pos_s.count())} #Creating Empty Nested Dic
        for k in range(0,pos_s.count()):   #Inserting Values into that Dic
            id = str(pos_s[k]["_id"])
            user_obj[k]["so_id"] = id
            user_obj[k]["po_id"] = pos_s[k]["po_id"]
            user_obj[k]["so_sx"] = pos_s[k]["so_sx"]
            user_obj[k]["so_rx"] = pos_s[k]["so_rx"]
            user_obj[k]["org"] = pos_s[k]["org"]
            user_obj[k]["loc_ship"] = pos_s[k]["loc_ship"]
            user_obj[k]["quant"] = pos_s[k]["quant"]
            user_obj[k]["amount"] = pos_s[k]["amount"]
            user_obj[k]["TC"] = pos_s[k]["TC"]
            user_obj[k]["Status"] = pos_s[k]["Status"]
            user_obj[k]["Date"] = pos_s[k]["Date"]
        response = jsonify({'ReturnMsg':'Success','user':user_obj}) 
        response.status_code = 200
    except Exception as e:
        print(e)
    return response




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
            own = db.users.find_one({'username':data['Data']['username']})
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
            user_obj["owned_assets"] = len(own["owned"])
            response = jsonify({'ReturnMsg':'Success','user':user_obj})
            response.status_code = 200
    except Exception as e:
        return bad_request(str(sys.exc_info()[0]) + " error on line no: " + str(sys.exc_info()[2].tb_lineno) + " Data received: " +  json.dumps(data))
    return response


@app.route('/api/services/v1/get_asset_list',methods = ['POST'])
def get_asset_list():
    response = jsonify({})
    response.status_code = 404
    try:
        app.logger.info("Inside get asset api")
        data = request.data
        data = json.loads(data)
        app.logger.info(data)
        if 'username' not in data['Data']:
            return bad_request('Username Not Found')
        own = db.users.find_one({'username':data['Data']['username']})
        user_obj = {}
        user_obj["owned_assets"] = own["owned"]
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

@app.route('/api/services/v1/get_priv_key',methods=["POST"])
def get_priv_key():
    try:
        resp = jsonify({})
        data = request.data
        data = json.loads(data)
        username = data["username"]
        print("In API")
        print(username)
        user_details = mongo.db.users.find_one({"username":username})
        # app.logger.info(user_details)
        if user_details:
            priv_key = user_details["private_key"]
        else:
            priv_key = None
            return bad_request("Not found")
        resp = {"priv_key":priv_key}
        resp = jsonify(resp)
        resp.status_code = 200
        return resp
    except:
        exc_type,exc_obj,exc_tb = sys.exc_info()
        app.logger.error(str(exc_type) + str(exc_tb.tb_lineno))


@app.route('/api/services/v1/getTrackingInfo', methods = ['POST'])
def get_tracking_info_api():
    return {}

@app.route('/api/services/v1/getUserInfo', methods = ['POST'])
def get_user_info():
    return {}

@app.route('/api/services/v1/getAnalyticsInfo', methods = ['POST'])
def get_analytics_info():
    return {}


@app.route('/api/services/v1/get_register', methods = ['POST'])
def get_register():
    response = jsonify({})
    response.status_code = 404
    try:
        data = json.loads(request.data)
        if (
            not ('Name' in data['Data'])
            or not ('Email' in data['Data'])
            or not ('Role' in data['Data'])
            or not ('Org' in data['Data'])
            or not ('Address' in data['Data'])
            or not ('City' in data['Data'])
            or not ('State' in data['Data'])
            or not ('Zip' in data['Data'])
        ):
            return bad_request("Content Incomplete Not Found")
        user = generate_keypair()
        pub_key = user.public_key
        priv_key = user.private_key
        password_hash = generate_password_hash("12345")
        mongo.db.users.insert(
            {
                "username": data['Data']['Name'],
                "email": data['Data']['Email'],
                "Role": data['Data']['Role'],
                "password_hash": password_hash,
                "public_key": pub_key,
                "private_key": priv_key,
            }
        )
        db.users.insert(
            {
                "username": data['Data']['Name'],
                "email": data['Data']['Email'],
                "Role": data['Data']['Role'],
                "Org": data['Data']['Org'],
                "location": data['Data']['City'],
                "State": data['Data']['State'],
                "details": data['Data']['Zip'],
                "owned": [],
                "lock": [],
            }
        )
        response = jsonify({"ReturnMsg": "Success"})
        status_code = 200
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        app.logger.error(str(e) + "on line no: " + exc_tb.tb_lineno)
        response,status_code = bad_request(
            str(sys.exc_info()[0])
            + " error on line no: "
            + str(sys.exc_info()[2].tb_lineno)
            + " Data received: "
            + json.dumps(data)
        )
    return response



@app.route('/api/services/v1/sold', methods = ['POST'])
def sold():
    response = jsonify({})
    response.status_code = 404
    try:
        app.logger.info("Inside Sold API")
        data = json.loads(request.data)
        if (not ('username' in data['Data']) or not ('serial_no' in data['Data'])):
            return bad_request('Username Not Found')
        
        priv_key = get_priv_key_by_username(data['Data']['username'])
        if priv_key is None:
            return bad_request("User not found")
        response = transfer_asset("NJB",data['Data']['serial_no'],priv_key)
        if response is not None:
            db.users.update_one({'username':"NJB" },{ '$addToSet': { 'owned':data['Data']['serial_no'] } } )
            db.users.update_one({'username':data['Data']["username"] },{ '$pull': { 'owned':data['Data']['serial_no'] } } )
            response = jsonify({"ReturnMsg":"Success", "transact":"true"})
            response.status_code = 200
        else:
            response = jsonify(response)
            response.status_code = 400
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        app.logger.error(str(e) + "on line no: " + exc_tb.tb_lineno)
        response,status_code = bad_request(
            str(sys.exc_info()[0])
            + " error on line no: "
            + str(sys.exc_info()[2].tb_lineno)
            + " Data received: "
            + json.dumps(data)
        )
    return response



@app.route('/api/services/v1/acquire', methods = ['POST'])
def acquire():
    response = jsonify({})
    response.status_code = 404
    try:
        app.logger.info("Inside Acquire API")
        data = json.loads(request.data)
        if (not ('username' in data['Data']) or not ('serial_no' in data['Data'])):
            return bad_request('Username Not Found')
        app.logger.info("passed 1 Acquire")
        username = str(data['Data']['username'])
        serial_no = str(data['Data']['serial_no'])
        app.logger.info(serial_no)
        priv_key = get_priv_key_by_username("NJB")
        app.logger.info(priv_key)
        if priv_key is None:
            return bad_request("User not found")
        app.logger.info("Inside Transfer Function")
        response = transfer_asset(username,serial_no,priv_key)
        app.logger.info(response)
        if response is not None:
            db.users.update_one({'username':username },{ '$addToSet': { 'owned':serial_no } } )
            db.users.update_one({'username':"NJB" },{ '$pull': { 'owned':serial_no } } )
            response = jsonify({"ReturnMsg":"Success", "transact":"true"})
            response.status_code = 200
        else:
            response = jsonify(response)
            response.status_code = 400
    except Exception as e:
        eror = str(e)
        app.logger.info("Error")
        app.logger.info(eror)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        app.logger.error(str(e) + "on line no: " + str(exc_tb.tb_lineno))
        bad_request(eror +" Line " + str(exc_tb.tb_lineno))
        #response,status_code = bad_request(
            #str(sys.exc_info()[0])
            #+ " error on line no: "
           # + str(sys.exc_info()[2].tb_lineno)
          #  + " Data received: "
         #   + json.dumps(data)
        #)
    return response
