from flask import render_template, flash, redirect, url_for, request, session
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


bdb_root_url = 'localhost:9984'

bdb = BigchainDB(bdb_root_url)

# #buggy code starts here
def transfer_asset(form,username):
    results = bdb.assets.get(search = form.serialnumber.data)
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
            broker = mongo.db.users.find_one({'username':form.username.data})
            pub_key_broker = broker['public_key']
            # manu = mongo.db.users.find_one({'username':username})
            priv_key_manu = form.private_key.data
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
            
            bdb.transactions.send_commit(fulfilled_transfer_tx)
            return True
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
            broker = mongo.db.users.find_one({'username':form.username.data})
            pub_key_broker = broker['public_key']
            manu = mongo.db.users.find_one({'username':username})
            priv_key_manu = form.private_key.data
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
            bdb.transactions.send_commit(fulfilled_transfer_tx)
            return True
            

            
#non buggy code starts here
def search_asset(form):
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

def createasset(form, username):
    t = datetime.utcnow()
    sack = {
        'data': {
            'sack': {
                'serial_number': form.serialnumber.data,
                'manufacturer': username,
            },
        },
    }
    metadata = {'cost': form.cost.data, 'timestamp': str(t)}

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
        prepared_creation_tx, private_keys=form.private_key.data)


        bdb.transactions.send_commit(fulfilled_creation_tx)
        return True
    except:
        flash("Something went wrong")
        return False

#non buggy code ends here


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
        create = createasset(form,session["username"])
        if create:
           flash("Asset created succesfully")
           return redirect(url_for('create_assets'))
    return render_template('manufacturer.html', form = form)


@app.route('/transaction', methods=['GET', 'POST'])
@login_required
def transaction():
    form = BrokerForm()
    if form.validate_on_submit():
        transact = transfer_asset(form,session["username"])
        if transact:
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

