from rq import get_current_job
from app import app,db,mongo
from app.models import User,Task
from .utils import *

import sys
ASSETS_PER_TRANS = app.config.get("ASSETS_PER_TRANS",2000)

def create_n_assets(username,serial_no,cost,priv_key,n):
    for i in range(n):
        createasset(username,serial_no,cost,priv_key)
    # mongo.db.tasks.update({"id":task_id},{'$set': {"complete":True}})

def create_asset_async(username,serial_no,cost,priv_key,no):
    try:
        user = mongo.db.users.find_one({"username":username})
        user_obj = User(user)
        _set_task_progress(0)
        while no > ASSETS_PER_TRANS:
            user_obj.launch_task("create_n_assets",f"CREATE task queued for {ASSETS_PER_TRANS} assets",
                                    username,serial_no,cost,priv_key,ASSETS_PER_TRANS)
            no -= ASSETS_PER_TRANS
        
        user_obj.launch_task("create_n_assets",f"CREATE task queued for {no} assets",
                                username,serial_no,cost,priv_key,no)
        return True
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
        return False
    finally:
        _set_task_progress(100)

def transfer_n_assets(username,serial_no,priv_key,n):
    for i in range(n):
        transfer_asset(username,serial_no,priv_key)

def transfer_asset_async(username,serial_no,priv_key,no):
    try:
        user = mongo.db.users.find_one({"username":username})
        user_obj = User(user)
        _set_task_progress(0)
        while no > ASSETS_PER_TRANS:
            user_obj.launch_task("transfer_n_assets",f"TRANSFER task queued for {ASSETS_PER_TRANS} assets",
            username,serial_no,priv_key,ASSETS_PER_TRANS)
            no -= ASSETS_PER_TRANS
        user_obj.launch_task("transfer_n_assets",f"TRANSFER task queued for {ASSETS_PER_TRANS} assets",
            username,serial_no,priv_key,no)
        return True
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
        return False
    finally:
        _set_task_progress(100)

    return True
def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = mongo.db.tasks.find_one(job.get_id())
        # task["user"].add_notification('task_progress', {'task_id': job.get_id(), 'progress': progress})
        if progress >= 100:
            task["complete"] = True
        task.update()