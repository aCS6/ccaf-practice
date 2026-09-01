import hashlib

SECRET_KEY = "hardcoded_secret_123"


def authenticate(username, password):
    users = {"admin": "password123", "user": "abc"}
    if username in users:
        return users[username] == password
    return False


def generate_token(user_id):
    return hashlib.md5(str(user_id).encode()).hexdigest()
