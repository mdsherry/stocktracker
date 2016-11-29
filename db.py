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

    def get_most_recent_transaction(self):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM transactions ORDER BY dt desc LIMIT 1")
        return cur.fetchone()

    def get_transaction_count(self):
        cur = self.db.cursor()
        cur.execute("SELECT count(*) FROM transactions")
        return cur.fetchone()[0]

    def add_transaction(self, transaction):
        cur = self.db.cursor()
        size_id = [var['value_id'] for var in transaction['variations'] if var['property_id'] == 100]
        cur.execute("INSERT INTO transactions (transaction_id, listing_id, size_id, dt) VALUES (?, ?, ?, ?)",
            (transaction['transaction_id'], transaction['listing_id'], size_id[0] if size_id else 0, transaction['creation_tsz']))
        self.db.commit()

    def add_listing(self, listing):
        cur = self.db.cursor()
        cur.execute("INSERT OR REPLACE INTO listings (listing_id, title, url) VALUES (?, ?, ?)", (listing['listing_id'], listing['title'], listing['url']))
        self.db.commit()

    def add_variation(self, listing_id, variation):
        cur = self.db.cursor()
        for option in variation['options']:
            cur.execute("INSERT OR REPLACE INTO product_variation VALUES (?, ?, ?, ?)",
                (listing_id, variation['formatted_name'], option['value'], option['value_id']))
        self.db.commit()


    def get_recent_transactions(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT
                transactions.dt, listings.title, listings.url, product_variation.variation_value
            FROM
                transactions
                JOIN listings USING (listing_id)
                JOIN product_variation ON product_variation.listing_id = transactions.listing_id AND product_variation.variation_id = transactions.size_id
            ORDER BY transactions.dt desc
            LIMIT 25
        """)
        return cur.fetchall()

    def get_listings(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT
                listings.title, listings.listing_id, product_variation.variation_value, product_variation.variation_id, COUNT(variation_to_stock.stock_id) as stock_count
            FROM
                listings
                JOIN product_variation USING (listing_id)
                LEFT JOIN variation_to_stock USING (listing_id, variation_id)
            GROUP BY
                1,2,3,4
        """)
        return cur.fetchall()

    def get_listing(self, listing_id, variation_id):
        cur = self.db.cursor()
        cur.execute("""
            SELECT
                listings.title, listings.listing_id, product_variation.variation_value, product_variation.variation_id
            FROM
                listings
                JOIN product_variation USING (listing_id)
            WHERE listing_id = ? AND variation_id = ?
        """, (listing_id, variation_id))
        return cur.fetchone()

    def get_linked_stock(self, listing_id, variation_id):
        cur = self.db.cursor()
        cur.execute("""
            SELECT
                stocked_item.*, variation_to_stock.count as stock_used
            FROM
                stocked_item
                JOIN variation_to_stock ON stocked_item.id = variation_to_stock.stock_id
            WHERE
               listing_id = ? AND variation_id = ?
        """, (listing_id, variation_id))
        return cur.fetchall()

    def set_linked_stock(self, listing_id, variation_id, linked_stock):
        cur = self.db.cursor()
        cur.execute("DELETE FROM variation_to_stock WHERE listing_id = ? AND variation_id = ?", (listing_id, variation_id))
        for (stock_id, count) in linked_stock:
            cur.execute("INSERT INTO variation_to_stock VALUES (?, ?, ?, ?)", (listing_id, variation_id, stock_id, count))
        self.db.commit()

    def update_stock_count(self, transaction):
        cur = self.db.cursor()
        size_id = [var['value_id'] for var in transaction['variations'] if var['property_id'] == 100]
        if size_id:
            size_id = size_id[0]
        else:
            size_id = 0
        cur.execute("SELECT * FROM variation_to_stock WHERE listing_id = ? AND variation_id = ?", (transaction['listing_id'], size_id))
        stock = cur.fetchall()
        for item in stock:
            cur.execute("UPDATE stocked_item SET count = count - ? WHERE id = ?", (item['count'], item['stock_id']))
        self.db.commit()