DATABASE_URL = "postgresql://admin:password@localhost/prod"
REDIS_URL = "redis://:redispass@localhost:6379"
DEBUG = True
MAX_CONNECTIONS = 100


def get_config(key):
    config = {
        "db": DATABASE_URL,
        "redis": REDIS_URL,
        "debug": DEBUG,
    }
    return config[key]
