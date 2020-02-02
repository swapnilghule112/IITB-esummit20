from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from time import sleep
from sys import exit

bdb_root_url = ''
bdb = BigchainDB('http://localhost:9984')
user1 = generate_keypair()
user2= generate_keypair()

sack = {
    'data': {
        'sack': {
            'serial_number': '5431abc',
            'manufacturer': 'user1',
            },
        },
    }
metadata = {
    'size': '4', 
    'price': '2500'
    }

prepared_creation_tx = bdb.transactions.prepare(
        operation='CREATE',
        signers=user1.public_key,
        asset=sack,
        metadata=metadata,
    )

fulfilled_creation_tx = bdb.transactions.fulfill(prepared_creation_tx, private_keys=user1.private_key)

#checking
sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
# --> True
#________________________________________________________________________________________________________________________
#Transcation id

txid = fulfilled_creation_tx['id']
#txid

#accepting transaction
fulfilled_transfer_tx = bdb.transactions.fulfill(
        prepared_transfer_tx,
        private_keys=user1.private_key,
)

sent_transfer_tx = bdb.transactions.send_commit(fulfilled_transfer_tx)

#checking
sent_transfer_tx == fulfilled_transfer_tx
#-->True

#checking
fulfilled_transfer_tx['outputs'][0]['public_keys'][0] == user2.public_key
#-->True


