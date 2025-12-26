import json
import numpy as np
import urllib.parse
import logging
import discord
import datetime

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

def make_embed_history(matches):
    # Prepare blue embed
    embed = discord.Embed(
        title=f"Lastest games:",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Match history")

    # Add one field per match
    for match_time, account, details in matches:
        # Convert ms -> UTC datetime
        dt = datetime.datetime.fromtimestamp(match_time / 1000, tz=datetime.timezone.utc)
        date_str = dt.strftime('%d-%m-%Y %H:%M UTC')

        win_emoji = "🟢" if details['win'] else "🔴"
        line = (
            f"{date_str} — {account.game_name}#{account.tag_line}\n"
            f"{win_emoji} **{details['champion']}** ({details['queue']})\n"
            f"K/D/A: {details['kills']}/{details['deaths']}/{details['assists']} • {details['duration_min']} min"
        )

        embed.add_field(name="\u200b", value=line, inline=False)

    return embed