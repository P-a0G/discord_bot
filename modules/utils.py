import json
import numpy as np
import urllib.parse
import logging
import os

logging.basicConfig(encoding='utf-8', level=logging.INFO)


def read_json(path):
    with open(path, 'r', encoding='utf-8-sig') as fi:
        data = json.load(fi)

    return data


def write_json(path, data):
    with open(path, 'w', encoding='utf-8-sig') as fo:
        json.dump(data, fo, ensure_ascii=False, indent=4, default=convert)


def convert(o):
    if isinstance(o, str):
        return o
    elif isinstance(o, int):
        return o
    elif isinstance(o, np.int32) or isinstance(o, np.int64):
        return int(o)
    print(type(o))
    raise TypeError


def is_valid_url(url):
    print("url?", url)
    # Parse the URL using urllib.parse
    parsed_url = urllib.parse.urlparse(url)

    # Check if the scheme and netloc (domain name) are non-empty
    if all([parsed_url.scheme, parsed_url.netloc]):
        logging.info(" > valid url")
        return 1
    else:
        logging.info(" > url not valid")
        return 0


def get_size(file_pth):
    return round(os.path.getsize(file_pth) / 1048576, 2)


def show_message_info(message):
    print("message:", message)
    print("id:", message.id)
    print("channel:", message.channel)
    print("type:", message.type)

    print("author:")
    print("\t id:", message.author.id)
    print("\t name:", message.author.name)

    print("content:", message.content)
