from app import login,mongo
from flask_login import UserMixin
import json

class User(UserMixin):
    username = ""
    def __init__(self,user_json):
        self.user_json = user_json

    def get_id(self):
        self.username = self.user_json.get('username')
        object_id = self.user_json.get('_id')
        return str(object_id)
    
    def __repr__(self):
        return f'{self.user_json}'

@login.user_loader
def load_user(user_id):
    users = mongo.db.users
    user_json = users.find_one({'_id': 'ObjectId(user_id)'})
    return User(user_json)