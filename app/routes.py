from flask import render_template, flash, redirect, url_for, request, session,jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, ManufacturerForm, BrokerForm, SearchForm
from app import app, mongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.models import User
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from datetime import datetime
from werkzeug.http import HTTP_STATUS_CODES


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
    pass

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
        return None


            
#non buggy code starts here
def search_asset(form):
    try:
        result = bdb.assets.get(search = form.search.data)
        if result:
            creation_tx = bdb.transactions.get(asset_id = result[0]['id'])
            if creation_tx:
                # print(type(creation_tx))
                return creation_tx
            else:
                return None
        else:
            flash("no results were found for this query")
    except Exception:
        return None

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
            flash("Something went wrong")
            return None
    
    except Exception:
        return None


@app.route('/')
@app.route('/index')
@login_required
def index():
    # return redirect(url_for('manufacturer'))
    return render_template('index.html', title='Home')



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
            return render_template('index.html', title='Sign In',role = role_,form=form)
        return redirect(next_page)         
    return render_template('login.html', title='Sign In',role = role_,form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        users = mongo.db.users
        existing_user = users.find_one({'username': form.username.data})

        if existing_user:
            flash('That username already exists..Try something else')
        else:
            user = generate_keypair()
            pub_key = user.public_key
            priv_key = user.private_key
            password_hash = generate_password_hash(form.password.data)
            users.insert({'username': form.username.data,'email': form.email.data,'Role':form.role.data, 'password_hash': password_hash, 'public_key': pub_key, 'private_key': priv_key})
            # u = users.find_one({'username': form.username.data})
            # login_user(u)
            flash(f'Remember and keep your private key in a safe place {priv_key}')
            return redirect(url_for('index'))
    
    return render_template('register.html',title = 'Register', form =form)



@app.route('/manufacture',methods=['GET', 'POST'])
@login_required
def create_assets():
    # print(session)    
    form = ManufacturerForm()
    if form.validate_on_submit():
        serial_no = form.serialnumber.data
        cost = form.cost.data
        private_key = form.private_key.data
        for i in range(1000):
            create = createasset(session["username"],serial_no,cost,private_key)
        if create is not None:
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
        transact = transfer_asset(session["username"],serial_no,priv_key)
        if transact is not None:
            flash('Transaction completed!!')
        else:
            flash('Transaction failed because asset was not found')
    return render_template('transaction.html', form = form)



@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        result = search_asset(form)
        if result is None:
            flash("not found")
        else:
            # flash(result)
            return render_template('result.html', result=result)
    return render_template('search.html', form = form)


# API routes starts from here

@app.route('/api/services/v1/getUserDetails', methods = ['POST'])
def get_user_details_api():
    data = request.get_json() or {}
    user = mongo.db.users.find_one({'username':data['Data']['username']})

    if ('username' not in data['Data'] or 'password' not in data['Data']):
        return bad_request('must include username and password fields')

    if user is None:
        return bad_request('Username does not exist')

    if check_password_hash(user['password_hash'],data['Data']['password']):
        return bad_request('Password not matching')
    
    response = jsonify({'ReturnMsg':'Success','user':user})
    response.status_code = 200
    return response


@app.route('/api/services/v1/creatAsset',methods = ['POST'])
def create_asset_api():
    data = request.get_json() or {}
    if 'serial_no' not in data['Data'] or 'number_of_assets' not in data['Data'] or 'cost' not in data['Data'] or 'username' not in data['Data'] or 'private_key' not in data['Data']:
        return bad_request('One or more missing fields')
    
    response = createasset(data['Data']['username'],data['Data']['serial_no'], data['Data']['cost'],data['Data']['private_key'])
    if response is None:
        return bad_request('Failed')
    
    response = (response)
    response.status_code = 200
    return response

@app.route('/api/services/v1/transferAsset',methods = ['POST'])
def transfer_asset_api():
    data = request.get_json() or {}
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
    return {}

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
