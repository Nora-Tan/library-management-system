import sys,os
from os.path import dirname, abspath
# from xmlrpc.client import boolean

basedir = dirname(abspath(dirname(__file__)))
sys.path.insert(0, dirname(dirname((abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# from common.import login_manager
from common.models import Book, Inventory, ReadBook

from nameko.rpc import rpc, RpcProxy

# all service connect to one db
engine = create_engine('sqlite:///' + os.path.join(basedir, 'data.sqlite'), echo=True)

class BookService(object):
    name = "book"
    register_rpc = RpcProxy("book")

    def __init__(self) -> None:
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

    @rpc
    def book(self):
        return self.session.query(Book), Book()
    
    @rpc
    def get_read_book_by_start_date(self,str_start_date):
        return self.session.query(ReadBook).filter(start_date=str_start_date).count()
    
    @rpc
    def get_read_book_by_end_date(self, str_end_date):
        return self.session.query(ReadBook).filter(end_date=str_end_date).count()

    @rpc
    def get_read_book_by_barcode_and_card_id(self, barcode, card):
        return self.session.query.filter(ReadBook.barcode == barcode,
                                         ReadBook.card_id == card, ReadBook.end_date.is_(None)).first()
    
    @rpc
    def get_book_by_book_name(self, book_name):
        return self.session.query(Book).filter(Book.book_name.like(book_name)).all()
    
    @rpc
    def get_book_by_book_author(self, author_name):
        return self.session.query(Book).filter(Book.author.contains(author_name)).all()

    @rpc
    def get_book_by_class_name(self, class_name):
        return self.session.query(Book).filter(Book.class_name.contains(class_name)).all()

    @rpc
    def get_book_by_isbn_all(self, isbn):
        return self.session.query(Book).filter(Book.isbn.contains(isbn)).all()

    @rpc
    def get_book_by_isbn(self, isbn_str):
        return self.session.query(Book).filter(isbn=isbn_str).first()
    
    @rpc
    def get_books_by_book_name(self, book_name):
        return self.session.query(Book).join(Inventory).filter(Book.book_name.contains(book_name),
                                                              Inventory.status == 1).with_entities(Inventory.barcode, Book.isbn, Book.book_name, Book.author, Book.press).\
            all()
    @rpc
    def get_books_by_card_id(self, card_id):
        return self.session.query(ReadBook).join(Inventory).join(Book).filter(ReadBook.card_id == card_id,
                                                                     ReadBook.end_date.is_(None)).with_entities(ReadBook.barcode, Book.isbn, Book.book_name, ReadBook.start_date,
                                                                                                                ReadBook.due_date).all()
    @rpc 
    def get_records_by_card_id(self, card_id):
        return self.session.query(ReadBook).join(Inventory).join(Book).filter(ReadBook.card_id == card_id)\
            .with_entities(ReadBook.barcode, Inventory.isbn, Book.book_name, Book.author, ReadBook.start_date,
                           ReadBook.end_date, ReadBook.due_date).all()


