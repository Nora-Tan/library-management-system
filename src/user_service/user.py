import sys,os
import json

from os.path import dirname, abspath
basedir = dirname(abspath(dirname(__file__)))
sys.path.insert(0, dirname(dirname((abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.models import Admin, Student
from flask import jsonify

from nameko.rpc import rpc, RpcProxy

# all service connect to one db
engine = create_engine('sqlite:///' + os.path.join(basedir, 'data.sqlite'), echo=True)

class UserService(object):
    name = "user"
    register_rpc = RpcProxy("user")
    
    def __init__(self) -> None:
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

    @rpc
    def get_admin_user(self,admin_id,password):
        
        user = self.session.query(Admin).filter_by(admin_id=admin_id, password=password).first()
        # user_dict = user.to_dict()
        # return json.dumps(user_dict)
        return json.dumps({"admin_id": user.admin_id, "admin_name": user.admin_name, "password": user.password, "right": user.right})

    @rpc
    def get_admin_user_by_id(self,user_id):
        user = self.session.query(Admin).filter_by(admin_id=user_id).first()
        user_dict = user.to_dict()
        return json.dumps(user_dict)

    @rpc
    def get_sutdent_by_card_id(self, card_id):
        return self.session.query(Student).filter(card_id=card_id).first()
    
    def module_to_dict(self, module):
        return {key: getattr(module, key) for key in module.__all__}

