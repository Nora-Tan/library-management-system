import sys,os
import json

from os.path import dirname, abspath

basedir = dirname(abspath(dirname(__file__)))
sys.path.insert(0, dirname(dirname((abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.models import Inventory
from nameko.rpc import rpc, RpcProxy


# all service connect to one db
engine = create_engine('sqlite:///' + os.path.join(basedir, 'data.sqlite'), echo=True)

class InventoryService(object):
    name = "inventory"
    register_rpc = RpcProxy("inventory")
    
    def __init__(self) -> None:
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

    @rpc
    def get_count_by_isbn(self,isbn,status=False):
        if status:
            return self.session.query(Inventory).filter(isbn=isbn, status=True).count()
        return self.session.query(Inventory).filter(isbn=isbn).count()

    @rpc
    def get_inventory_by_barcode(self, barcode):
        return self.session.query(Inventory).filter(barcode=barcode).first()
