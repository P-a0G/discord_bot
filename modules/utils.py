import json
import numpy as np
import urllib.parse
import logging

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
    # Parse the URL using urllib.parse
    parsed_url = urllib.parse.urlparse(url)

    # Check if the scheme and netloc (domain name) are non-empty
    if all([parsed_url.scheme, parsed_url.netloc]):
        logging.info(" > valid url")
        return 1
    else:
        logging.info(" > url not valid")
        return 0


def is_duration_in_range(duration_str, min_minutes=2, max_minutes=6):
    if isinstance(duration_str, int):
        duration_str = str(duration_str)

    # Remove "PT" prefix
    duration_str = duration_str[2:]

    # Initialize variables
    hours = 0
    minutes = 0
    seconds = 0

    # Extract hours, minutes, and seconds
    if 'H' in duration_str:
        hours_str, duration_str = duration_str.split('H')
        hours = int(hours_str)
    if 'M' in duration_str:
        minutes_str, duration_str = duration_str.split('M')
        minutes = int(minutes_str)
    if 'S' in duration_str:
        seconds_str = duration_str.split('S')[0]
        seconds = int(seconds_str)

    # Calculate total duration in minutes
    total_minutes = hours * 60 + minutes + seconds / 60

    # Check if duration is within the range
    return min_minutes <= total_minutes <= max_minutes


def show_message_info(message):
    print("message:", message)
    print("id:", message.id)
    print("channel:", message.channel)
    print("type:", message.type)

    print("author:")
    print("\t id:", message.author.id)
    print("\t name:", message.author.name)

    print("content:", message.content)
