import sqlite3
import argparse
import smtplib
from email.mime.text import MIMEText
import time

import arrow
import schedule

from db import DB
import etsy
import config

def load_listings():
    db = DB(sqlite3.connect("database.db"))
    e = etsy.Etsy(config)
    for listing in e.get_listings(config.site):
        print ("Adding listing " + listing['title'])
        db.add_listing(listing)
        for variation in e.get_variations(listing['listing_id']):
            db.add_variation(listing['listing_id'], variation)

def load_transactions(since=None):
    db = DB(sqlite3.connect("database.db"))
    e = etsy.Etsy(config)
    for transaction in e.get_transactions(config.site, since):
        try:
            db.add_transaction(transaction)
            db.update_stock_count(transaction)
        except sqlite3.IntegrityError:
            pass

def load_new_transactions(since=None):
    db = DB(sqlite3.connect("database.db"))
    most_recent = db.get_most_recent_transaction()
    most_recent_datetime = arrow.get(most_recent[3])
    most_recent_date = most_recent_datetime.humanize()
    print("Most recent transaction: " + most_recent_date)
    return load_transactions(most_recent[3])



def generate_stock():
    db = sqlite3.connect("database.db")
    landscape_sizes = ["20x16", "24x18"]
    portrait_sizes = ["16x20", "18x24"]
    landscape = ["Mario Still Life", "Zelda Still Life", "Pokemon Still Life", "Animal Crossing Still Life", "Ace Attorney Still Life"]
    portrait = ["Link Portrait", "Zelda Portrait", "Katamari Royal Portrait", "Megaman Family Portrait", "Princess Peach Portrait"]
    cur = db.cursor()
    for prnt in landscape:
        for size in landscape_sizes:
            cur.execute("INSERT INTO stocked_item (name, description, count) VALUES (?, ?, ?)", ("{} {}".format(prnt, size), "", 0))
    for prnt in portrait:
        for size in portrait_sizes:
            cur.execute("INSERT INTO stocked_item (name, description, count) VALUES (?, ?, ?)", ("{} {}".format(prnt, size), "", 0))
    db.commit()

def init_db():
    db = sqlite3.connect("database.db")
    with open('schema.sql', 'r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def send_report():
    db = sqlite3.connect("database.db")
    cur = db.cursor()
    cur.execute("SELECT * FROM stocked_item WHERE count < ?", (config.stock_threshold,))
    low_stock = cur.fetchall()
    if low_stock:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(config.email_username, config.email_password)
        low_stock_list = ["<li>{} ({})</li>".format(item[1], item[3]) for item in low_stock]
        me = "mdsherry@gmail.com"
        you = "lizsherry@gmail.com"
        html = """<html><head></head><body>
        The following items are running low:
        <ul>
        {low_stock}
        </ul>
        </body></html>""".format(low_stock='\n'.join(low_stock_list))
        msg = MIMEText(html, 'html')
        msg['Subject'] = "Etsy Stock Report"
        msg['From'] = me
        msg['To'] = you
        server.send_message(msg)
        server.quit()

def monitor():
    schedule.every().hour.do(load_new_transactions)
    schedule.every().day.at("18:00").do(send_report)
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description="A tool to bulk load data from the Etsy API")
    parser.add_argument("mode", choices=["init-all", "load-listings", "load-transactions", "load-new-transactions", "generate-stock", "send-report", "monitor"])
    args = parser.parse_args()
    if args.mode == "init-all":
        init_db()
        load_listings()
        generate_stock()
    elif args.mode == "load-listings":
        load_listings()
    elif args.mode == "load-transactions":
        load_transactions()
    elif args.mode == "load-new-transactions":
        load_new_transactions()
    elif args.mode == "generate-stock":
        generate_stock()
    elif args.mode == "send-report":
        send_report()
    elif args.mode == "monitor":
        monitor()

if __name__ == '__main__':
    main()