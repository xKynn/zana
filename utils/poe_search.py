import poe.utils as utils

from cachetools import cached
from .cache import cache

class POEClientException(Exception):
    pass

@cached(cache)
def find_one(name: str, client, loop):
    print(name)
    if 1:
        item = client.find_items({'_pageName': name}, limit=1)
        if item:
            return item[0]
        else:
            item = client.find_passives({'name': name}, limit=1)
            if item:
                return item[0]
            else:
                return None
    else:
        return POEClientException

@cached(cache)
def cache_pob_xml(xml, client):
    stats = utils.parse_pob_xml(xml, client)
    return stats