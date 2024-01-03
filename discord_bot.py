import os

import discord
from utils import is_valid_url, extract_from_url, get_size, read_json, write_json
import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

anniversary_dict_path = "anniversary.json"
if os.path.exists(anniversary_dict_path):
    anniversaries = read_json(anniversary_dict_path)
else:
    anniversaries = dict()


@client.event
async def on_ready():
    print('Bot is ready to go!')


@client.event
async def on_message(message):
    # print("id:", message.id)
    # print("channel:", message.channel)
    # print("type:", message.type)
    # print("author:", message.author)
    # print("content:", message.content)

    if message.content.startswith("set birthday"):
        _, _, anniversary, user = message.content.split(" ")
        try:
            day, mounth, year = anniversary.split("/")
            day = int(day)
            mounth = int(mounth)
            year = int(year)

        except ValueError:
            await message.channel.send("Format invalide, utiliser: '!set birthday DD/MM/YYYY User'.")
            return

        if not 0 < day < 32:
            await message.channel.send("Mettre la date au format: DD/MM/YYYY")
            return
        if not 0 < mounth < 13:
            await message.channel.send("Mettre la date au format: DD/MM/YYYY")
            return

        anniversaries[user] = {
            "day": day,
            "mounth": mounth,
            "year": year
        }
        write_json(anniversary_dict_path, anniversaries)
        await message.channel.send("Saved")
        return

    if not (str(message.channel) == "Direct Message with Unknown User" or "bot" in str(message.channel)):
        return
    
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

    if is_valid_url(message.content):
        await message.channel.send('Downloading file to mp3....')

        try:
            file_pth = extract_from_url(message.content, add_tags=False)
        except ValueError as e:
            await message.channel.send(f'\t\tSorry I couldn\'t get the music')
            await message.channel.send(f'Error: {e}')

        if file_pth is None:
            await message.channel.send(f'\t\tSorry I couldn\'t get the music')
            return

        file_size = get_size(file_pth)
        await message.channel.send(f'\t\tFile saved locally, size = {file_size}Mo')

        if file_size > 8:
            await message.channel.send(f'File is too large to be sent')
        else:
            file = discord.File(file_pth)
            await message.channel.send(file=file)

# token = read_json("tokens.json")["Flash_bot"]
token = read_json("tokens.json")["debug"]
client.run(token)


