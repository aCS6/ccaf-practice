cache = {}


def get_cache(key):
    return cache.get(key, None)


def set_cache(key, value, ttl=None):
    cache[key] = value


def invalidate_all():
    cache = {}
