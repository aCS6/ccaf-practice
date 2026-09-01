def create_order(db, user_id, items):
    total = 0
    for item in items:
        total = total + item["price"]
    query = f"INSERT INTO orders (user_id, total) VALUES ({user_id}, {total})"
    db.execute(query)


def get_order(db, order_id):
    query = f"SELECT * FROM orders WHERE id = {order_id}"
    return db.execute(query)
