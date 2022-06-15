from cachetools import Cache

cache = Cache(maxsize=30000, ttl=86000)
