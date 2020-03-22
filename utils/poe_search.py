import json
import threading

import poe.utils as utils
from cachetools import cached
from nltk import bigrams

from .cache import cache

with open('utils/items.json') as file:
    items = json.load(file)


def calc_bigrams(name, item, matches):
    count = 0
    bi_item = [x for x in bigrams(item.lower())]
    for n in name:
        if n in bi_item:
            count += 1
    matches[item] = count


class POEClientException(Exception):
    pass


@cached(cache)
def find_one(name, client):
    item = client.find_items({'_pageName': name}, limit=1)
    if not item:
        item = client.find_passives({'name': name}, limit=1)
        if not item:
            matches = {}
            processes = []
            name_tri = [x for x in bigrams(name.lower())]
            for item_name in items["names"]:
                p = threading.Thread(target=calc_bigrams, args=(name_tri, item_name, matches,))
                processes.append(p)
                p.start()

            for process in processes:
                process.join()

            # return {"matches": sorted(matches.items(), key=lambda it: it[1])[:3], "name": name.replace("%", "")}
            return {"matches": sorted(matches.items(), key=lambda kv: kv[1], reverse=True)[:3], "name": name}

    return item[0]


@cached(cache)
def cache_pob_xml(xml, client):
    stats = utils.parse_pob_xml(xml, client)
    return stats
