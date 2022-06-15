from cachetools import TTLCache

cache = TTLCache(maxsize=30000, ttl=86000)
