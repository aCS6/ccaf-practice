import pickle


def save_report(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def load_report(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def generate_report(db, user_id):
    query = f"SELECT * FROM reports WHERE user_id = {user_id}"
    results = []
    for row in db.execute(query):
        results.append(row)
    return results
