# jute Supply Chain Management system

# Team Houdini

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






