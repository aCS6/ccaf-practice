LOG_FILE = "/var/log/app.log"


def log(level, message, user_data=None):
    if user_data:
        print(f"[{level}] {message} user={user_data}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{level}] {message}\n")


def get_logs():
    results = []
    for line in open(LOG_FILE):
        results.append(line)
    return results
