import poe.utils as utils
import threading
import json
from Levenshtein import StringMatcher

levenshtein = StringMatcher.StringMatcher()

from cachetools import cached
from .cache import cache

with open('utils/items.json') as f:
    items = json.load(f)


def calc_levenshtein(name, item, matches):
    d = StringMatcher.StringMatcher(seq1=name.lower(), seq2=item.lower()).distance()
    if d <= 3:
        matches[item] = d

class POEClientException(Exception):
    pass


@cached(cache)
def find_one(name: str, client, loop):
    if 1:
        item = client.find_items({'_pageName': name}, limit=1)
        if not item:
            item = client.find_passives({'name': name}, limit=1)
            if not item:
                matches = {}
                processes = []
                for item_name in items["names"]:
                    p = threading.Thread(target=calc_levenshtein, args=(name.replace("%", ""), item_name, matches,))
                    processes.append(p)
                    p.start()

                for process in processes:
                    process.join()

                return {"matches": sorted(matches.items(), key=lambda it: it[1])[:3], "name": name.replace("%", "")}

        return item[0]
    else:
        return POEClientException

@cached(cache)
def cache_pob_xml(xml, client):
    stats = utils.parse_pob_xml(xml, client)
    return stats