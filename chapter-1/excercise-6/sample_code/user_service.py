def get_user(db, user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)


def delete_user(db, user_id):
    query = f"DELETE FROM users WHERE id = {user_id}"
    db.execute(query)


def list_users(db):
    results = []
    for row in db.execute("SELECT * FROM users"):
        results.append(row)
    return results
