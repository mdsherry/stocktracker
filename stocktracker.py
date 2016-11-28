import pprint
import sqlite3

from flask import Flask, request, render_template, g, redirect, url_for
from forms import StockForm
from db import DB

app = Flask(__name__)

DATABASE = 'database.db'

def init_db():
    with app.app_context():
        db = get_db().db
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = DB(sqlite3.connect(DATABASE))
        db.db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.db.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stock")
def list_stock():
    return render_template("stock.html", stock=get_db().get_all_stock())

@app.route("/stock/new", methods=['GET'])
def new_stock():
    return render_template("new_stock.html", form=StockForm())

@app.route("/stock/new", methods=['POST'])
def submit_new_stock():
    form = StockForm()
    if form.validate_on_submit():
        get_db().add_stock(form)
        return redirect(url_for('list_stock'))
    return render_template("new_stock.html", form=form)

@app.route("/stock/<int:stock_id>", methods=['GET'])
def edit_stock(stock_id):
    stock_item = get_db().get_stock(stock_id)
    form = StockForm(name=stock_item['name'], description=stock_item['description'], count=stock_item['count'])
    return render_template("edit_stock.html", form=form, stock_id=stock_id)

@app.route("/stock/<int:stock_id>", methods=['POST'])
def submit_edit_stock(stock_id):
    form = StockForm()
    if form.validate_on_submit():
        get_db().update_stock(stock_id, form)
        return redirect(url_for('list_stock'))
    return render_template("edit_stock.html", form=form, stock_id=stock_id)

if __name__ == '__main__':
    app.secret_key = r'Hh\xba\xf0\xbb\x17\xe5\x132\xf8\xb3E\r\xf0.$N\x95"\xbe%P`W'
    app.run(debug=True)