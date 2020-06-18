from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from config import Config
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
login.login_view = 'login'
mongo = PyMongo(app)
bootstrap = Bootstrap(app)

from app import routes
