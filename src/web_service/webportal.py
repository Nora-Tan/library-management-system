
import os,sys
import json
from os.path import dirname, abspath
from flask import Flask, render_template
from nameko.standalone.rpc import ClusterRpcProxy

basedir = dirname(abspath(dirname(__file__)))
sys.path.insert(0, dirname(dirname((abspath(__file__)))))

from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user,LoginManager
from web_service.forms import Login, SearchBookForm, ChangePasswordForm, EditInfoForm, SearchStudentForm, NewStoreForm, StoreForm, BorrowForm
from common.db import db,init_app
from common.models import Book, Inventory, ReadBook
import time, datetime
from nameko.rpc import RpcProxy
from flask_script import Manager


# app = init_app()

template_dir = os.path.abspath('./templates')

app = Flask(__name__,template_folder=template_dir)
manager = Manager(app)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'basic'
login_manager.login_view = 'login'
login_manager.login_message = "Please login first."

nameko_username = os.environ.get('nameko_username')
nameko_password = os.environ.get('nameko_password')
nameko_host = os.environ.get('nameko_host', "rabbitmq")
CONFIG = {'AMQP_URI': f"amqp://{nameko_username}:{nameko_password}@{nameko_host}"}



@login_manager.user_loader
@app.route('/', methods=['GET', 'POST'])
def login():
    print(template_dir)
    form = Login()
    if form.validate_on_submit():
        with ClusterRpcProxy(CONFIG) as user_rpc:
            user = user_rpc.user.get_admin_user(admin_id=form.account.data, password=form.password.data)
            user = json.loads(user)
        if user is None:
            flash('Incorrect account number or password!')
            return redirect(url_for('.login'))
        else:
            login_user(user) 
            session['admin_id'] = user.admin_id
            session['name'] = user.admin_name
            return redirect(url_for('.index'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You are logged out!')
    return redirect(url_for('.login'))


@app.route('/index')
@login_required
def index():
    return render_template('index.html', name=session.get('name'))

@app.route('/echarts')
@login_required
def echarts():
    days = []
    num = []
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    ten_ago = int(today_stamp) - 9 * 86400
    for i in range(0, 10):
        with ClusterRpcProxy(CONFIG) as book_rpc:
            borr = book_rpc.get_read_book_by_start_date(str((ten_ago+i*86400)*1000))
            retu = book_rpc.get_read_book_by_end_date(str((ten_ago+i*86400)*1000))
        num.append(borr + retu)
        days.append(timeStamp((ten_ago+i*86400)*1000))
    data = []
    for i in range(0, 10):
        item = {'name': days[i], 'num': num[i]}
        data.append(item)
    return jsonify(data)


@app.route('/user/<id>')
@login_required
def user_info(id):
    with ClusterRpcProxy(CONFIG) as user_rpc:
        user = user_rpc.user.get_admin_user_by_id(user_id=id)

    return render_template('user-info.html', user=user, name=session.get('name'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.password2.data != form.password.data:
        flash(u'Two times the password is not the same!')
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash(u'Password modified successfully!')
            return redirect(url_for('.index'))
        else:
            flash(u'The original password was entered incorrectly, and the modification failed!')
    return render_template("change-password.html", form=form)


@app.route('/change_info', methods=['GET', 'POST'])
@login_required
def change_info():
    form = EditInfoForm()
    if form.validate_on_submit():
        current_user.admin_name = form.name.data
        db.session.add(current_user)
        flash(u'Personal information has been successfully modified!')
        return redirect(url_for('.user_info', id=current_user.admin_id))
    form.name.data = current_user.admin_name
    id = current_user.admin_id
    right = current_user.right
    return render_template('change-info.html', form=form, id=id, right=right)


@app.route('/search_book', methods=['GET', 'POST'])
@login_required
def search_book():
    form = SearchBookForm()
    return render_template('search-book.html', name=session.get('name'), form=form)


@app.route('/books', methods=['POST'])
def find_book():
    def find_name():
        with ClusterRpcProxy(CONFIG) as book_rpc:
            return book_rpc.get_book_by_book_name('%'+request.form.get('content')+'%')

    def find_author():
        with ClusterRpcProxy(CONFIG) as book_rpc:
            return book_rpc.get_book_by_book_author(request.form.get('content'))

    def find_class():
        with ClusterRpcProxy(CONFIG) as book_rpc:
            return book_rpc.get_book_by_class_name(request.form.get('content'))

    def find_isbn():
        with ClusterRpcProxy(CONFIG) as book_rpc:
            return book_rpc.get_book_by_isbn_all(request.form.get('content'))

    methods = {
        'book_name': find_name,
        'author': find_author,
        'class_name': find_class,
        'isbn': find_isbn
    }
    books = methods[request.form.get('method')]()
    data = []
    for book in books:
        with ClusterRpcProxy(CONFIG) as inventory_rpc:
            count = inventory_rpc.get_count_by_isbn(isbn=book.isbn)
            available = inventory_rpc.get_count_by_isbn(isbn=book.isbn, status=True)
        item = {'isbn': book.isbn, 'book_name': book.book_name, 'press': book.press, 'author': book.author,
                'class_name': book.class_name, 'count': count, 'available': available}
        data.append(item)
    return jsonify(data)


@app.route('/user/book', methods=['GET', 'POST'])
def user_book():
    form = SearchBookForm()
    return render_template('user-book.html', form=form)

@app.route('/search_student', methods=['GET', 'POST'])
@login_required
def search_student():
    form = SearchStudentForm()
    return render_template('search-student.html', name=session.get('name'), form=form)


def timeStamp(timeNum):
    if timeNum is None:
        return timeNum
    else:
        timeStamp = float(float(timeNum)/1000)
        timeArray = time.localtime(timeStamp)
        print(time.strftime("%Y-%m-%d", timeArray))
        return time.strftime("%Y-%m-%d", timeArray)


@app.route('/student', methods=['POST'])
def find_student():
    with ClusterRpcProxy(CONFIG) as user_rpc:
        stu = user_rpc.get_sutdent_by_card_id(card_id=request.form.get('card'))
    if stu is None:
        return jsonify([])
    else:
        valid_date = timeStamp(stu.valid_date)
        return jsonify([{'name': stu.student_name, 'gender': stu.sex, 'valid_date': valid_date, 'debt': stu.debt}])


@app.route('/record', methods=['POST'])
def find_record():
    with ClusterRpcProxy(CONFIG) as book_rpc:
        records = book_rpc.get_records_by_card_id(request.form.get('card'))
    data = []
    for record in records:
        start_date = timeStamp(record.start_date)
        due_date = timeStamp(record.due_date)
        end_date = timeStamp(record.end_date)
        if end_date is None:
            end_date = 'Not returned'
        item = {'barcode': record.barcode, 'book_name': record.book_name, 'author': record.author,
                'start_date': start_date, 'due_date': due_date, 'end_date': end_date}
        data.append(item)
    return jsonify(data)


@app.route('/user/student', methods=['GET', 'POST'])
def user_student():
    form = SearchStudentForm()
    return render_template('user-student.html', form=form)


@app.route('/storage', methods=['GET', 'POST'])
@login_required
def storage():
    form = StoreForm()
    if form.validate_on_submit():
        with ClusterRpcProxy(CONFIG) as rpc:
            book = rpc.get_book_by_isbn(isbn=request.form.get('isbn'))
            exist = rpc.get_inventory_by_barcode(barcode = request.form.get('barcode'))
        if book is None:
            flash(u'The addition fails, please note whether the book information has been entered, if not registered, please enter the information in the New Book Collection window.')
        else:
            if len(request.form.get('barcode')) != 6:
                flash(u'The book encoding length is incorrect')
            else:
                if exist is not None:
                    flash(u'The number already exists!')
                else:
                    item = Inventory()
                    item.barcode = request.form.get('barcode')
                    item.isbn = request.form.get('isbn')
                    item.admin = current_user.admin_id
                    item.location = request.form.get('location')
                    item.status = True
                    item.withdraw = False
                    today_date = datetime.date.today()
                    today_str = today_date.strftime("%Y-%m-%d")
                    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
                    item.storage_date = int(today_stamp)*1000
                    db.session.add(item)
                    db.session.commit()
                    flash(u'Book storage successful!')
        return redirect(url_for('.storage'))
    return render_template('storage.html', name=session.get('name'), form=form)


@app.route('/new_store', methods=['GET', 'POST'])
@login_required
def new_store():
    form = NewStoreForm()
    if form.validate_on_submit():
        if len(request.form.get('isbn')) != 13:
            flash(u'ISBN Length error')
        else:
            with ClusterRpcProxy(CONFIG) as book_rpc:
                exist = book_rpc.get_book_by_isbn(isbn = request.form.get('isbn'))
            if exist is not None:
                flash(u'The book information already exists, please check it before entering it, or fill in the library form.')
            else:
                book = Book()
                book.isbn = request.form.get('isbn')
                book.book_name = request.form.get('book_name')
                book.press = request.form.get('press')
                book.author = request.form.get('author')
                book.class_name = request.form.get('class_name')
                db.session.add(book)
                db.session.commit()
                flash(u'Book information added successfully!')
        return redirect(url_for('.new_store'))
    return render_template('new-store.html', name=session.get('name'), form=form)


@app.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow():
    form = BorrowForm()
    return render_template('borrow.html', name=session.get('name'), form=form)


@app.route('/find_stu_book', methods=['GET', 'POST'])
def find_stu_book():
    with ClusterRpcProxy(CONFIG) as user_rpc:
        stu = user_rpc.get_sutdent_by_card_id(card_id=request.form.get('card'))
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    if stu is None:
        return jsonify([{'stu': 0}])  # Not Found
    if stu.debt is True:
        return jsonify([{'stu': 1}])  # Overdue
    if int(stu.valid_date) < int(today_stamp)*1000:
        return jsonify([{'stu': 2}])  # expire
    if stu.loss is True:
        return jsonify([{'stu': 3}])  # Reported lost
    with ClusterRpcProxy(CONFIG) as book_rpc:
        books = book_rpc.get_books_by_book_name(request.form.get('book_name'))
    data = []
    for book in books:
        item = {'barcode': book.barcode, 'isbn': book.isbn, 'book_name': book.book_name,
                'author': book.author, 'press': book.press}
        data.append(item)
    return jsonify(data)


@app.route('/out', methods=['GET', 'POST'])
@login_required
def out():
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    barcode = request.args.get('barcode')
    card = request.args.get('card')
    book_name = request.args.get('book_name')
    readbook = ReadBook()
    readbook.barcode = barcode
    readbook.card_id = card
    readbook.start_date = int(today_stamp)*1000
    readbook.due_date = (int(today_stamp)+40*86400)*1000
    readbook.borrow_admin = current_user.admin_id
    db.session.add(readbook)
    db.session.commit()
    with ClusterRpcProxy(CONFIG) as rpc:
        book = rpc.get_inventory_by_barcode(barcode=barcode)
        book.status = False
        db.session.add(book)
        db.session.commit()
        bks = rpc.get_books_by_book_name(request.form.get('book_name'))
    data = []
    for bk in bks:
        item = {'barcode': bk.barcode, 'isbn': bk.isbn, 'book_name': bk.book_name,
                'author': bk.author, 'press': bk.press}
        data.append(item)
    return jsonify(data)


@app.route('/return', methods=['GET', 'POST'])
@login_required
def return_book():
    form = SearchStudentForm()
    return render_template('return.html', name=session.get('name'), form=form)


@app.route('/find_not_return_book', methods=['GET', 'POST'])
def find_not_return_book():
    with ClusterRpcProxy(CONFIG) as user_rpc:
        stu = user_rpc.get_sutdent_by_card_id(card_id=request.form.get('card'))
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    if stu is None:
        return jsonify([{'stu': 0}])  # Not Found
    if stu.debt is True:
        return jsonify([{'stu': 1}])  # Overdue
    if int(stu.valid_date) < int(today_stamp)*1000:
        return jsonify([{'stu': 2}])  # expire
    if stu.loss is True:
        return jsonify([{'stu': 3}])  # Reported lost
    with ClusterRpcProxy(CONFIG) as book_rpc:
        books = book_rpc.get_books_by_card_id(request.form.get('card'))
    data = []
    for book in books:
        start_date = timeStamp(book.start_date)
        due_date = timeStamp(book.due_date)
        item = {'barcode': book.barcode, 'isbn': book.isbn, 'book_name': book.book_name,
                'start_date': start_date, 'due_date': due_date}
        data.append(item)
    return jsonify(data)


@app.route('/in', methods=['GET', 'POST'])
@login_required
def bookin():
    barcode = request.args.get('barcode')
    card = request.args.get('card')
    with ClusterRpcProxy(CONFIG) as book_rpc:
        record = book_rpc.get_read_book_by_barcode_and_card_id(barcode == barcode, card == card)

    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    record.end_date = int(today_stamp)*1000
    record.return_admin = current_user.admin_id
    db.session.add(record)
    db.session.commit()
    with ClusterRpcProxy(CONFIG) as rpc:
        book = rpc.get_inventory_by_barcode(barcode=barcode)
    book.status = True
    db.session.add(book)
    db.session.commit()
    with ClusterRpcProxy(CONFIG) as rpc:
        bks = rpc.get_books_by_card_id(card)
    data = []
    for bk in bks:
        start_date = timeStamp(bk.start_date)
        due_date = timeStamp(bk.due_date)
        item = {'barcode': bk.barcode, 'isbn': bk.isbn, 'book_name': bk.book_name,
                'start_date': start_date, 'due_date': due_date}
        data.append(item)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
