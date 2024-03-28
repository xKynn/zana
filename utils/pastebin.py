import base64
import re
import urllib.request
import zlib

from urllib.request import Request,urlopen

"""
Original from: https://github.com/aggixx/PoBPreviewBot/blob/master/util.py 
            && https://github.com/aggixx/PoBPreviewBot/blob/master/pastebin.py
"""


def fetch_paste_key(content):
    """
    Fetches the last paste key in a message.
    :param content: message.content
    :return: paste key to retrieve pastebin content
    """
    if 'raw' in content:
        content = content.replace('raw/', '')
    regex = r"pastebin.com\/(\S*)"
    results = re.findall(regex, content)
    return results

def fetch_pobb_key(content):
    """
    Fetches the last paste key in a message.
    :param content: message.content
    :return: paste key to retrieve pastebin content
    """
    if 'raw' in content:
        content = content.replace('raw/', '')
    regex = r"pobb.in\/(\S*)"
    results = re.findall(regex, content)
    return results


def decode_base64_and_inflate(b64string):

    decoded_data = base64.b64decode(b64string)
    return zlib.decompress(decoded_data)


def decode_to_xml(enc):
    enc = enc.replace("-", "+").replace("_", "/")
    xml_str = None
    xml_str = decode_base64_and_inflate(enc)
    return xml_str


def get_raw_data(url):
    url = urllib.request.urlopen(url)
    return url.read().decode('utf-8')  # read and encode as utf-8


def get_as_xml(paste_key):
    raw_url = 'https://pastebin.com/raw/' + paste_key
    data = get_raw_data(raw_url)
    return decode_to_xml(data)

def get_as_xml_pobb(paste_key):
    raw_url = 'https://pobb.in/pob/' + paste_key
    req = Request(raw_url)
    req.add_header('User-Agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246")
    content = urlopen(req).read().decode('utf-8')
    return decode_to_xml(content)