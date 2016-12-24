import pprint
import sqlite3

import arrow
from flask import Flask, request, render_template, g, redirect, url_for
from forms import StockForm

from db import DB
import etsy
import config

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

@app.route("/transactions", methods=["GET"])
def show_transactions():
    transaction_count = get_db().get_transaction_count()
    most_recent_transaction = get_db().get_most_recent_transaction()
    if most_recent_transaction:
        most_recent_datetime = arrow.get(most_recent_transaction['dt'])
        most_recent_date = most_recent_datetime.humanize()
        datepicker_date = most_recent_datetime.format("YYYY/MM/DD")
    else:
        most_recent_date = "never"
        datepicker_date = ""
    recent_transactions = get_db().get_recent_transactions()
    return render_template("update_transactions.html",
                           transaction_count=transaction_count,
                           most_recent_transaction=most_recent_date,
                           datepicker_most_recent=datepicker_date,
                           recent_transactions=recent_transactions)

@app.route("/transactions", methods=["POST"])
def update_transactions():
    # TODO: Make this asynchronous
    if 'date' in request.form and request.form['date']:
        date = arrow.get(request.form['date']).timestamp
    else:
        date = None
    e = etsy.Etsy(config)
    db = get_db()
    for transaction in e.get_transactions(config.site, date):
        db.add_transaction(transaction)
        db.update_stock_count(transaction)
    return redirect(url_for('show_transactions'))

@app.route("/listings")
def get_listings():
    return render_template("listings.html.j2", listings=get_db().get_listings())

@app.route("/listings/<int:listing_id>/<int:variation_id>", methods=["GET"])
def link_stock(listing_id, variation_id):
    listing = get_db().get_listing(listing_id, variation_id)
    linked_stock = get_db().get_linked_stock(listing_id, variation_id)
    return render_template("link_listing.html.j2",
        listing=listing, linked_stock=linked_stock, linked_count=len(linked_stock), listing_id=listing_id, variation_id=variation_id, stock=get_db().get_all_stock())

@app.route("/listings/<int:listing_id>/<int:variation_id>", methods=["POST"])
def do_link_stock(listing_id, variation_id):
    linked_stock = []
    added = set()
    for i in range(1, 6):
        if request.form['stock_{}'.format(i)] and request.form['required_{}'.format(i)]:
            try:
                count = int(request.form['required_{}'.format(i)])
                stock_id = int(request.form['stock_{}'.format(i)])
                if stock_id not in added and count > 0:
                    linked_stock.append((stock_id, count))
                    added.add(stock_id)

            except ValueError:
                pass
    get_db().set_linked_stock(listing_id, variation_id, linked_stock)
    return redirect(url_for('get_listings'))

@app.template_filter('format_date')
def format_date(dt):
    return arrow.get(dt).format("YYYY/MM/DD")
@app.template_filter('format_datetime')
def format_date(dt):
    return arrow.get(dt).format("YYYY/MM/DD hh:mm")
if __name__ == '__main__':
    app.secret_key = r'Hh\xba\xf0\xbb\x17\xe5\x132\xf8\xb3E\r\xf0.$N\x95"\xbe%P`W'
    app.run(debug=True)
