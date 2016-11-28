import sqlite3

class DB(object):
    def __init__(self, db):
        self.db = db
    def get_all_stock(self):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM stocked_item");
        return cur.fetchall()

    def get_stock(self, stock_id):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM stocked_item WHERE id = ?", (stock_id,));
        return cur.fetchone()

    def add_stock(self, form):
        cur = self.db.cursor()
        cur.execute("INSERT INTO stocked_item (name, description, count) VALUES (?, ?, ?)", (form.name.data, form.description.data, form.count.data))
        self.db.commit()

    def update_stock(self, stock_id, form):
        cur = self.db.cursor()
        cur.execute("UPDATE stocked_item SET name = ?, description = ?, count = ? WHERE id = ?", (form.name.data, form.description.data, form.count.data, stock_id))
        self.db.commit()
