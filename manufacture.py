from bigchaindb_driver import BigchainDB

bdb_root_url = "localhost:9984"

bdb = BigchainDB(bdb_root_url)
bicycle = ""
serial_number = ""
manufacturer = ""
size = ""
metadata = ""
alice_public_key = ""


def createasset(asset_name):
    serial_number = input("Enter BIS Serial Number: ")
    manufacturer = input("Enter MFG name: ")
    size = input("Enter Jute Bag Size:")
    bicycle = {
        "data": {
            "bicycle": {"serial_number": serial_number, "manufacturer": manufacturer}
        }
    }
    metadata = {"Size": size}
    print(bicycle, "\n", metadata)
    return True


def prepared_creation():
    prepared_creation_tx = bdb.transactions.prepare(
        operation="CREATE", signers=alice.public_key, asset=bicycle, metadata=metadata
    )
    return True


def fullfilcreation():
    print("Successfullycreatedyourasset")
    fulfilled_creation_tx = bdb.transactions.fulfill(
        prepared_creation_tx, private_keys=alice.private_key
    )
    return True


def creationcommit():
    sent_creation_tx = bdb.transactions.send_commit(fulfilled_creation_tx)
    print("Successfullycommitteedd")
    return True


asset_name = "bicycle"
create = createasset(asset_name)
if create:
    prep = prepared_creation()
    if prep:
        fullfil = fullfilcreation()
        if fullfil:
            comit = creationcommit()
