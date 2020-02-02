import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    MONGO_URI = 'mongodb://localhost:27017/bigchain'
    MONGO_DBNAME = 'bigchain'
