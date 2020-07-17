from app import app,login,mongo,db,redis_app,task_queue
from flask_login import UserMixin
import json
import redis
import rq

class User(UserMixin):
    username = ""
    def __init__(self,user_json):
        self.user_json = user_json

    def get_id(self):
        self.username = self.user_json.get('username')
        object_id = self.user_json.get('_id')
        return str(object_id)
    def launch_task(self, name, description, *args, **kwargs):
        app.logger.info("Task queue")
        app.logger.info(task_queue)
        # app.logger.info(dir(task_queue))
        # app.logger.info(*args)
        # app.logger.info(**kwargs)
        # app.logger.info('app.tasks.'+ name)
        # app.logger.info(self)
        if name == "create_n_assets":
            from app.tasks import create_n_assets
            rq_job = task_queue.enqueue(create_n_assets, *args, **kwargs)
        elif name == "transfer_n_assets":
            from app.tasks import transfer_n_assets
            rq_job = task_queue.enqueue(transfer_n_assets, *args, **kwargs)
        app.logger.info("RQ JOB")
        app.logger.info(rq_job)
        task = Task(id=rq_job.get_id(), name=name, description=description, user_id=self.username)
        mongo.db.tasks.insert({"name":name,"description":description,"user_id":self.username,"id":rq_job.get_id(),"complete":False})
        return task

    def get_tasks_in_progress(self):
        result = mongo.db.tasks.find({"user":self.username,"complete":False})
        return result

    def get_task_in_progress(self, name):
        result = mongo.db.tasks.find_one({"name":name,"user_id":self.username,"complete":False})
        return result

    def __repr__(self):
        return f'{self.user_json}'

class Task():
    def __init__(self,id,name,description,user_id):
        self.id = id
        self.name = name
        self.user_id = user_id
        self.description = description
        self.complete = False
    
    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=redis_app)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
    
    def __repr__(self):
        task_obj = {
            "id" : self.id,
            "name": self.name,
            "user_id": self.user_id,
            "description": self.description,
            "complete": self.complete
        }
        return task_obj


@login.user_loader
def load_user(user_id):
    users = mongo.db.users
    user_json = users.find_one({'_id': 'ObjectId(user_id)'})
    return User(user_json)
