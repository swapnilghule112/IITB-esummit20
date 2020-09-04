# Jute Supply Chain Management system

## Team RestFull

## Clone this repository and do:

# Set Up BigchainDB, MongoDB and Tendermint

We now install and configure software that must run
in every BigchainDB node: BigchainDB Server,
MongoDB and Tendermint.

## Install BigchainDB Server

BigchainDB Server requires **Python 3.6+**, so make sure your system has it.

Install the required OS-level packages:

```
# For Ubuntu 18.04:
sudo apt install -y python3-pip libssl-dev
# Ubuntu 16.04, and other Linux distros, may require other packages or more packages
```

Check that you installed the correct version of BigchainDB Server using `bigchaindb --version`.

## Configure BigchainDB Server

To configure BigchainDB Server, run:

```
bigchaindb configure
```


## Install (and Start) MongoDB
```
sudo apt install mongodb
```
## Install Tendermint

```
sudo apt install -y unzip
wget https://github.com/tendermint/tendermint/releases/download/v0.31.5/tendermint_v0.31.5_linux_amd64.zip
unzip tendermint_v0.31.5_linux_amd64.zip
rm tendermint_v0.31.5_linux_amd64.zip
sudo mv tendermint /usr/local/bin
```

## Start Configuring Tendermint
```
tendermint init
```

## Install flask and other dependancies using requirements.txt
```
pip install -r requirements.txt
```

## To run the app:

- Start Mongodb
- Start bigchaindb server
``` bigchaindb start
```

- Start flask app
```
export FLASK_APP=supply_chain.py
flask run
```

### Server should be live on localhost:5000


## API documentation - SIH - 2020

By Swapnil Ghule

### send data in base64 encoded form

### 1. Login (POST)

description: authentication service

url: /api/services/v1/getUserDetails

headers: Content-Type: application/json

data:{'Data':{'username':username,'password':password}}

return code 200 success
            500 internal server error
            404 not found

sample request:
sample response:


### 2. Create Asset (POST)

description: Create an asset for a given user. All fields are mandatory.

 url /api/services/v1/creatAsset
 
 headers: Content-Type: application/json
 
 data:{'Data':{'serial_no':serial_no, 'number_of_assets':number_of_assets, 'cost':cost,'username':username, 'private_key':private_key}}
 
 return code 200 success
             401 Not authorized
             500 internal server error
             404 not found

sample request:
sample response:


### 3. Transfer Asset (POST)

description: Transfer an asset for a given user. All fields are mandatory.


 url /api/services/v1/transferAsset
 
 headers: Content-Type: application/json
 
 data:{'Data':{'buyer_username':buyer_username,        'serial_number':serial_number,'public_key':pub_key,'number_of_assets':number_of_assets, 'private_key':private_key}}
 
 return code 200 success
             401 Not authorized
             500 internal server error
             404 not found

sample request:
sample response:


### 4. Search(GET)

description:

url /api/services/v1/search

 headers: Content-Type: application/json
 
 data:{'Data':{'serial_no':serial_no}}
 
 return code 200 success
             500 internal server error
             404 not found

sample request:
sample response:


### 5. GetCurrentOwnedAssets (POST)

description:

 url /api/services/v1/getCurrentOwnedAssets
 
 headers: Content-Type: application/json
 
 data:{'Data':{'pub_key':pub_key, 'priv_key':priv_key}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 6. GetTrackingInfo (POST)

description:

 url /api/services/v1/getTrackingInfo
 
 headers: Content-Type: application/json
 
 data:{'Data':{'':serial_no}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:

### 7. GetUserInfo (POST)

description:

 url /api/services/v1/getUserInfo
 
 headers: Content-Type: application/json
 
 data:{'Data':{'':serial_no}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:

### 8. GetAnalyticsInfo (POST)
description:

 url /api/services/v1/getAnalyticsInfo
 
 headers: Content-Type: application/json
 
 data:{'Data':{'':serial_no}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:




