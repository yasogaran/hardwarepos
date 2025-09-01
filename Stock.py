from DB import connect_db
from Product import Product

class Stock:
    def __init__(self, sid, pid):
        self.sid = sid
        self.pid = pid
        cur, con = connect_db()

        cur.execute("SELECT * FROM Products WHERE pid=%s", (self.pid,))
        records = cur.fetchone()
        if records:
            self.product = Product(records[1])
            self.status = records[2]
            self.created_at = records[3]
            self.updated_at = records[4]


