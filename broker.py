from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from time import sleep
from sys import exit


bdb_root_url = ' '  # Use YOUR BigchainDB Root URL here

bdb = BigchainDB(bdb_root_url)

user2 = generate_keypair()
txid = ''
block_height = bdb.blocks.get(txid=signed_tx['id'])
block = bdb.blocks.retrieve(str(block_height))
creation_tx = bdb.transactions.retrieve(txid)
fulfilled_creation_tx = creation_tx 
asset_id = creation_tx['id']
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
prepared_transfer_tx = bdb.transactions.prepare(
        operation='TRANSFER',
        asset=transfer_asset,
        inputs=transfer_input,
        recipients=user2.public_key,
)

