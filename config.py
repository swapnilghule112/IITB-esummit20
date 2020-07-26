import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    MONGO_URI = 'mongodb://localhost:27017/bigchain'
    MONGO_DBNAME = 'bigchain'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['swapnilghule2015@gmail.com','gothanepreyash@gmail.com','kunduosara@gmail.com']
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    ASSETS_PER_TRANS = 40
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
