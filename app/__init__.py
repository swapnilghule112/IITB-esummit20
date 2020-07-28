from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from config import Config
from flask_bootstrap import Bootstrap
from logging.handlers import RotatingFileHandler
import os
import logging
from logging.handlers import SMTPHandler
from pymongo import MongoClient
from redis import Redis
import rq

app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
login.login_view = "login"
mongo = PyMongo(app)
client = MongoClient(
    "mongodb+srv://Houdini:Houdini@clustermain-0hrue.mongodb.net/Houdini?retryWrites=true&w=majority"
)
db = client.get_database("trans")
bootstrap = Bootstrap(app)
redis_app = app.config.get("REDIS_URL", "redis://")
# task_queue = rq.Queue('jute-tasks', connection='redis://')
task_queue = rq.Queue("jute-tasks", connection=Redis.from_url("redis://"))

from app import routes, models, errors

if not app.debug:
    if app.config["MAIL_SERVER"]:
        auth = None
        if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
            auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
        secure = None
        if app.config["MAIL_USE_TLS"]:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
            fromaddr="no-reply@" + app.config["MAIL_SERVER"],
            toaddrs=app.config["ADMINS"],
            subject="Supply Chain Failure",
            credentials=auth,
            secure=secure,
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=10)
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s]: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Supply Chain Startup")
