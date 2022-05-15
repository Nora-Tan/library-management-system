from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from os.path import dirname, abspath
from sqlalchemy import create_engine

# engine=create_engine('sqlite:///:',echo=True)
basedir = dirname(abspath(dirname(__file__)))
db = SQLAlchemy()

login_manager = LoginManager()
login_manger=LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'login'
login_manager.login_message = u"请先login。"

def init_app():
    app = Flask("app")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    app.config["SECRET_KEY"] = '103c65c36fff4d1a874c999190494780'
    #app.config.from_object(config[config_name])
    #config[config_name].init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    return app

