import asyncio
import datetime
import os
from concurrent.futures import ThreadPoolExecutor

import discord
from discord.ext import commands, tasks

from modules.DataBase import database
from modules.MusicChannel import MusicChannel, extract_from_url, get_url_from_name
from modules.utils import read_json, is_valid_url

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

id_file = read_json("files/id_dict.json")

bot = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
daily_check = datetime.time(hour=2, minute=0, second=0, tzinfo=utc)


# todo autocompletion cf: https://www.youtube.com/watch?v=zSzFHxOkCfo&ab_channel=RichardSchwabe


@tasks.loop(time=daily_check)
async def check_for_new_musics():
    user_idx_list, artists_idx, artists_names = database.get_artists_idx_and_names()

    last_update = database.get_last_update_datetime()

    if last_update.date() == datetime.date.today():
        print("\tCheck was done today, wait for tomorrow")
        return 1

    for user_idx, artist_idx, artist in zip(user_idx_list, artists_idx, artists_names):
        # videos = MusicChannel(artist).get_last_update(last_update=last_update)
        print("Checking for", artist)
        videos = MusicChannel(artist, idx=artist_idx).get_last_update(
            last_update=datetime.datetime.now() - datetime.timedelta(days=1, hours=2)
        )
        print("\tFound", len(videos), "new videos")
        for v in videos:
            if not v.path or not os.path.exists(v.path):
                print("Didn't get", v.url)
                continue

            file = discord.File(v.path)
            print("\t\tNew released video downloaded:", v.path)

            await send_message_to_user(f'{v.url}', user_idx)
            await send_message_to_user(file, user_idx, is_file=True)

            v.delete()

    print("[Update done]")
    database.save_new_last_update()


@bot.command(name='daily')
async def daily_check_for_new_musics(ctx, days: int):
    if ctx.author.id != my_id:
        return

    user_idx_list, artists_idx, artists_names = database.get_artists_idx_and_names()

    last_update = datetime.datetime.now() - datetime.timedelta(days=days)

    await ctx.send(f"Doing a check for the last {days} days")

    for user_idx, artist_idx, artist in zip(user_idx_list, artists_idx, artists_names):
        print("Checking for", artist)
        videos = MusicChannel(artist, idx=artist_idx).get_last_update(
            last_update=last_update
        )
        print("\tFound", len(videos), "new videos")
        for v in videos:
            if not v.path or not os.path.exists(v.path):
                print("Didn't get", v.url)
                continue

            file = discord.File(v.path)
            print("\t\tNew released video downloaded:", v.path)

            await send_message_to_user(f'{v.url}', user_idx)
            await send_message_to_user(file, user_idx, is_file=True)

            v.delete()

    print("[Update done]")
    database.save_new_last_update()

    await ctx.send(f"{days} days check done")


@bot.event
async def on_ready():
    print('Bot is ready to go!')

    if not check_for_new_musics.is_running():
        check_for_new_musics.start()


@bot.command(name='sub')
async def subscribe(ctx, *, channel_name):
    channel_name = channel_name.strip()

    artist_idx = MusicChannel(channel_name).idx

    if database.is_artist_idx_in_db(ctx.author.id, artist_idx):
        await ctx.send("Had it already ;)")
        return

    database.add_artist_to_db(ctx.author.id, artist_idx, channel_name)
    await ctx.send(f"Registered {channel_name}")


@bot.command(name='unsub')
async def unsubscribe(ctx, *, channel_name):
    channel_name = channel_name.strip()

    artist_idx = MusicChannel(channel_name).idx

    artist_removed = database.remove_artist_from_db(ctx.author.id, artist_idx)

    if artist_removed:
        await ctx.send(f"{channel_name} removed from subscribed list")
    else:
        await ctx.send(f"{channel_name} wasn't in subscribed list")


executor = ThreadPoolExecutor()


@bot.command(name='get')
async def get_all_musics_from(ctx, *, args):
    if ' ' in args:
        *channel_name_parts, argument_2 = args.rsplit(' ', 1)
        if argument_2.isdigit():
            channel_name = ' '.join(channel_name_parts)
            n_max = int(argument_2)
        else:
            channel_name = args
            n_max = 10
    else:
        channel_name = args
        n_max = 10

    if ctx.author.id != my_id:
        return

    await ctx.send("Ok let's get a bunch of musics 😁")
    loop = asyncio.get_event_loop()
    musics = await loop.run_in_executor(executor, MusicChannel(channel_name).get_all)
    musics = musics[:n_max]

    if len(musics) == 0:
        await ctx.send(f"Couldn't find {channel_name}")
        return

    await ctx.send(f"I found {len(musics)} musics!")
    for audio_file in musics:
        if audio_file.path is None:
            await ctx.send(f'\t\tSorry I couldn\'t get {audio_file.title}')
            continue

        if audio_file.size < 8:
            file = discord.File(audio_file.path)
            await ctx.send(
                f"{channel_name}: {audio_file.title} - {'{:,}'.format(audio_file.view_count).replace(',', ' ')} views")
            await ctx.send(file=file)

        audio_file.delete()

    await ctx.send("Done 😎")


@bot.command(name='dl')
async def download_music(ctx, *, music_name):
    await ctx.send('Ok looking for the music 🕵️‍♂️')
    loop = asyncio.get_event_loop()

    music_url = await loop.run_in_executor(executor, get_url_from_name, music_name)
    if music_url is None or music_url == "":
        await ctx.send(f"Couldn't find {music_name}")
        return

    await ctx.send(f'🎶 There it is! 🎶\n{music_url}')

    audio_file = await loop.run_in_executor(executor, extract_from_url, music_url)

    if audio_file.path is None:
        await ctx.send('\t\tSorry I couldn\'t get the music')
        return

    await ctx.send(f'\t\tFile saved locally, size = {audio_file.size}Mo')

    if audio_file.size > 8:
        await ctx.send('File is too large to be sent')
    else:
        file = discord.File(audio_file.path)
        await ctx.send(file=file)

        audio_file.delete()


async def send_message_to_me(message, is_file=False):
    user = bot.get_guild(int(id_file["guild_id"])).get_member(int(id_file["my_id"]))

    if user:
        if is_file:
            await user.send(file=message)
        else:
            await user.send(message)
    else:
        print("[Error] Couldn't send message to me")


async def send_message_to_user(message, user_id, is_file=False):
    try:
        # Fetch the user object by ID
        user = await bot.fetch_user(int(user_id))

        # Send the message or file
        if is_file:
            await user.send(file=message)
        else:
            await user.send(message)

    except Exception as e:
        user_name = bot.get_user(int(user_id)).name
        print(f"[Error] Couldn't send message to user {user_name} ({user_id}): {e}")


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.content.startswith("!"):
        return

    # show_message_info(message)

    if not (str(message.channel) == "Direct Message with Unknown User" or "bot" in str(message.channel)):
        return

    if message.author == bot.user:
        return

    if is_valid_url(message.content):
        await message.channel.send('Downloading file to mp3....')
        loop = asyncio.get_event_loop()
        audio_file = await loop.run_in_executor(executor, extract_from_url, message.content)

        if audio_file.path is None:
            await message.channel.send('\t\tSorry I couldn\'t get the music')
            return

        await message.channel.send(f'\t\tFile saved locally, size = {audio_file.size}Mo')

        if audio_file.size > 8:
            await message.channel.send('File is too large to be sent')
        else:
            file = discord.File(audio_file.path)
            await message.channel.send(file=file)

            audio_file.delete()

# @bot.event
# async def on_message(message):
#     if message.content.startswith("!"):
#         await bot.process_commands(message)
#     show_message_info(message)


if __name__ == '__main__':
    token = read_json("files/tokens.json")["Flash_bot"]
    my_id = int(id_file["my_id"])
    bot.run(token)

