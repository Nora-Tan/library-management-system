from flask_login import UserMixin
from sqlalchemy import Column, String, Boolean,Integer,ForeignKey
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()



class Admin(Base):
    __tablename__ = 'admin'
    admin_id = Column(String(6), primary_key=True)
    admin_name = Column(String(32))
    password = Column(String(24))
    right = Column(String(32))

    def __init__(self, admin_id, admin_name, password, right):
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.password = password
        self.right = right

    def get_id(self):
        return self.admin_id

    def verify_password(self, password):
        if password == self.password:
            return True
        else:
            return False

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

class Book(Base):
    __tablename__ = 'book'
    isbn = Column(String(13), primary_key=True)
    book_name = Column(String(64))
    author = Column(String(64))
    press = Column(String(32))
    class_name = Column(String(64))

    def __repr__(self):
        return '<Book %r>' % self.book_name


class Student(Base):
    __tablename__ = 'student'
    card_id = Column(String(8), primary_key=True)
    student_id = Column(String(9))
    student_name = Column(String(32))
    sex = Column(String(2))
    telephone = Column(String(11), nullable=True)
    enroll_date = Column(String(13))
    valid_date = Column(String(13))
    loss = Column(Boolean, default=False)  
    debt = Column(Boolean, default=False)

    def __repr__(self):
        return '<Student %r>' % self.student_name


class Inventory(Base):
    __tablename__ = 'inventory'
    barcode = Column(String(6), primary_key=True)
    isbn = Column(ForeignKey('book.isbn'))
    storage_date = Column(String(13))
    location = Column(String(32))
    withdraw = Column(Boolean, default=False)  
    status = Column(Boolean, default=True)  
    admin = Column(ForeignKey('admin.admin_id'))  

    def __repr__(self):
        return '<Inventory %r>' % self.barcode


class ReadBook(Base):
    __tablename__ = 'readbook'
    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(ForeignKey('inventory.barcode'), index=True)
    card_id = Column(ForeignKey('student.card_id'), index=True)
    start_date = Column(String(13))
    borrow_admin = Column(ForeignKey('admin.admin_id'))  
    end_date = Column(String(13), nullable=True)
    return_admin = Column(ForeignKey('admin.admin_id'))  
    due_date = Column(String(13))  # The end date

    def __repr__(self):
        return '<ReadBook %r>' % self.id


