# Jute Supply Chain Management system

## Team Houdini

## Clone this repository and do:

# Set Up BigchainDB, MongoDB and Tendermint

We now install and configure software that must run
in every BigchainDB node: BigchainDB Server,
MongoDB and Tendermint.

## Install BigchainDB Server

BigchainDB Server requires **Python 3.6+**, so make sure your system has it.

Install the required OS-level packages:

```sh
# For Ubuntu 18.04:
$ sudo apt install -y python3-pip libssl-dev
# Ubuntu 16.04, and other Linux distros, may require other packages or more packages
```

Check that you installed the correct version of BigchainDB Server using `bigchaindb --version`.

## Configure BigchainDB Server

To configure BigchainDB Server, run:

```sh
$ bigchaindb configure
```


## Install (and Start) MongoDB
```sh
$ sudo apt install mongodb
$ mongod
```
## Install Tendermint

```sh
$ sudo apt install -y unzip
$ wget https://github.com/tendermint/tendermint/releases/download/v0.31.5/tendermint_v0.31.5_linux_amd64.zip
$ unzip tendermint_v0.31.5_linux_amd64.zip
$ rm tendermint_v0.31.5_linux_amd64.zip
$ sudo mv tendermint /usr/local/bin
```

## Start Configuring Tendermint
```sh
$ tendermint init
```

## Install flask and other dependancies using requirements.txt
```sh
$ pip install -r requirements.txt
```

## Install Redis and start
```sh
$ sudo apt install redis
```


- Start Redis 
```sh
$ sudo systemctl restart redis
```

## Install Python library of redis:

- rq library 
```sh
$ pip install rq
```

## Starting Redis Worker 

- starting worker
```sh
$ rq worker jute-tasks
```

## To run the app:


- Start bigchaindb server
```sh
$ bigchaindb start
```

- Start flask app
```sh
$ export FLASK_APP=supply_chain.py
$ flask run
```
### Server should be live on localhost:5000

## API 
### send data in base64 encoded form

### 1. Login (POST)

description: authentication service

>url: /api/services/v1/getUserDetails

>headers: Content-Type: application/json

>data:{'Data':{'username':username , 'password':password}}

return code 200 success
            500 internal server error
            404 not found

sample request:
sample response:


### 2. Create Asset (POST)

description: Create an asset for a given user. All fields are mandatory.

 >url /api/services/v1/creatAsset
 
 >headers: Content-Type: application/json
 
 >data:{'Data':{'serial_no':serial_no, 'number_of_assets':number_of_assets, 'cost':cost,'username':username, 'private_key':private_key}}
 
 return code 200 success
             401 Not authorized
             500 internal server error
             404 not found

sample request:
sample response:


### 3. Transfer Asset (POST)

description: Transfer an asset for a given user. All fields are mandatory.


>url /api/services/v1/transferAsset
 
>headers: Content-Type: application/json
 
>data:{'Data':{'buyer_username':buyer_username, 'serial_number':serial_number,'public_key':pub_key,'number_of_assets':number_of_assets, 'private_key':private_key}}
 
return code 200 success
             401 Not authorized
             500 internal server error
             404 not found

sample request:
sample response:


### 4. Search(GET)

description:

>url /api/services/v1/search

>headers: Content-Type: application/json
 
>data:{'Data':{'serial_no':serial_no}}
 
 return code 200 success
             500 internal server error
             404 not found

sample request:
sample response:


### 5. GetCurrentOwnedAssets (POST)

description:

>url /api/services/v1/getCurrentOwnedAssets
 
>headers: Content-Type: application/json
 
>data:{'Data':{'pub_key':pub_key, 'priv_key':priv_key}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 6. GetTrackingInfo (POST)

description:

>url /api/services/v1/getTrackingInfo
 
>headers: Content-Type: application/json
 
>data:{'Data':{'':serial_no}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:

### 7. GetUserInfo (POST)

description:

>url /api/services/v1/getUserInfo
 
>headers: Content-Type: application/json
 
>data:{'Data':{'':serial_no}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:

### 8. GetAnalyticsInfo (POST)
description:

>url /api/services/v1/getAnalyticsInfo
 
>headers: Content-Type: application/json
 
>data:{'Data':{'':serial_no}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 9. GetAssetList (POST)
description:

>url /api/services/v1/get_asset_list
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username':session_user}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 10. Get PO Invoice (POST)
description:

>url /api/services/v1/get_po_invoice
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username':session_user, 'po_id': po_id }}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 11. Get SO Invoice (POST)
description:

>url /api/services/v1/get_so_invoice
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username':session_user, 'so_id': so_id }}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 12. Finalize Order (POST)
description:

>url /api/services/v1/order_finalize
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username':session_user, 'so_id': so_id }}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 13. Apply Sales Order (POST)
description:

>url /api/services/v1/get_sales_order
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username':session_user, 'po_id': po_id, 'so_rx': SoReceiver, 'org': Organisation, 'loc_ship': Shipping Address, 'TC': Terms }}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 14. Cancel Sales Order (POST)
description:

>url /api/services/v1/so_cancel
 
>headers: Content-Type: application/json
 
>data:{'Data':{'so_id': so_id}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 15. Purchase Order (POST)
description:

>url /api/services/v1/get_purchase_order
 
>headers: Content-Type: application/json
 
>data:{'Data':{'po_id': po_id}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 16. Cancel Purchase Order (POST)
description:

>url /api/services/v1/po_cancel
 
>headers: Content-Type: application/json
 
>data:{'Data':{'po_id': po_id}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 17. Accept Purchase Order (POST)
description:

>url /api/services/v1/po_accept
 
>headers: Content-Type: application/json
 
>data:{'Data':{'po_id': po_id}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 18. Recived PO Order (POST)
description:

>url /api/services/v1/po_notify_r
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username': current_user}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 19. Recived PO Order (POST)
description:

>url /api/services/v1/po_notify_s
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username': current_user}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 20. Recived PO Order (POST)
description:

>url /api/services/v1/so_notify_r
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username': current_user}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 21. Recived SO Order (POST)
description:

>url /api/services/v1/so_notify_r
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username': current_user}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


### 22. Sent SO Order (POST)
description:

>url /api/services/v1/so_notify_s
 
>headers: Content-Type: application/json
 
>data:{'Data':{'username': current_user}}

 return code 200 success
             401 Not authorized
             500 internal server error
             404 Not found

sample request:
sample response:


## Run 
