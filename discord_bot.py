import asyncio
import datetime
import os
from concurrent.futures import ThreadPoolExecutor

import discord
from discord.ext import commands, tasks

from modules.MusicChannel import MusicChannel, extract_from_url
from modules.utils import read_json, is_valid_url

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

id_file = read_json("files/id_dict.json")

bot = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
daily_check = datetime.time(hour=2, minute=0, second=0, tzinfo=utc)

subscribed_to_music = dict()


# todo autocompletion cf: https://www.youtube.com/watch?v=zSzFHxOkCfo&ab_channel=RichardSchwabe


@tasks.loop(time=daily_check)
async def check_for_new_musics():
    if os.path.exists("files/subscribed_artists.txt"):
        with open("files/subscribed_artists.txt", "r") as f:
            artists = [a.strip() for a in f.readlines()]
    else:
        artists = []

    try:
        with open("files/last_update.txt", "r") as f:
            last_update = datetime.datetime.strptime(f.read().strip(), "%Y-%m-%dT%H:%M:%SZ")
    except FileNotFoundError:
        print("\t[Error] couldn't get last update")
        return 0

    if last_update.date() == datetime.date.today():
        print("\tCheck was done today, wait for tomorrow")
        return 1

    for artist in artists:
        # videos = MusicChannel(artist).get_last_update(last_update=last_update)
        videos = MusicChannel(artist).get_last_update(last_update=datetime.datetime.now() - datetime.timedelta(days=1, hours=2))

        for v in videos:
            if not v.path or not os.path.exists(v.path):
                print("Didn't get", v.url)
                continue

            file = discord.File(v.path)
            print("\t\tNew released video downloaded:", v.path)

            await send_message_to_me(f'{v.url}')
            await send_message_to_me(file, is_file=True)

            v.delete()

    print("[Update done]")
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    with open("files/last_update.txt", "w") as file:
        file.write(formatted_datetime)


@bot.event
async def on_ready():
    # await check_for_new_musics()
    print('Bot is ready to go!')

    if not check_for_new_musics.is_running():
        await check_for_new_musics.start()


@bot.command(name='set')
async def set_music_dict(ctx):
    if (ctx.guild.id, ctx.author.id) not in subscribed_to_music.keys():
        subscribed_to_music[(ctx.guild.id, ctx.author.id)] = []

        user = bot.get_guild(ctx.guild.id).get_member(ctx.author.id)

        await user.send("Music set done")


@bot.command(name='sub')
async def subscribe(ctx, channel_name):
    channel_name = channel_name.strip().replace(" ", "")

    if os.path.exists("files/subscribed_artists.txt"):
        with open("files/subscribed_artists.txt", "r") as f:
            artists = [a.strip() for a in f.readlines()]
    else:
        artists = []

    if channel_name in artists:
        await ctx.send("Had it already ;)")
        return

    if ctx.author.id != my_id:
        await ctx.send("Sorry you can't do that, ask moderator for permission.")
        return

    with open("files/subscribed_artists.txt", "a") as f:
        f.write(channel_name + "\n")
    await ctx.send(f"Registered {channel_name}")


@bot.command(name='unsub')
async def unsubscribe(ctx, channel_name):
    channel_name = channel_name.strip().replace(" ", "")

    if os.path.exists("files/subscribed_artists.txt"):
        with open("files/subscribed_artists.txt", "r") as f:
            artists = [a.strip() for a in f.readlines()]
    else:
        artists = []

    if channel_name in artists:
        await ctx.send(f"Removing {channel_name} from subscribed list")

    else:
        await ctx.send(f"{channel_name} wasn't in subscribed list")
        return

    artists.remove(channel_name)
    artists.sort()

    with open("files/subscribed_artists.txt", "w") as f:
        for a in artists:
            f.write(a + "\n")

    await ctx.send("Done !")


executor = ThreadPoolExecutor()


@bot.command(name='get')
async def get_all_musics_from(ctx, channel_name, n_max=10):
    if ctx.author.id != my_id:
        return

    await ctx.send("Ok let's get a bunch of musics 😁")
    loop = asyncio.get_event_loop()
    musics = await loop.run_in_executor(executor, MusicChannel(channel_name).get_all)
    musics = musics[:n_max]

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


async def send_message_to_me(message, is_file=False):
    user = bot.get_guild(int(id_file["guild_id"])).get_member(int(id_file["my_id"]))

    if user:
        if is_file:
            await user.send(file=message)
        else:
            await user.send(message)
    else:
        print("[Error] Couldn't send message to me")


async def send_message_to_sub(message):
    for guild_id, user_id in subscribed_to_music.keys():
        user = bot.get_guild(guild_id).get_member(user_id)

        await user.send(message)


@bot.event
async def on_message(message):
    if message.content.startswith("!"):
        await bot.process_commands(message)
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
    # token = read_json("files/tokens.json")["Flash_bot"]
    my_id = int(id_file["my_id"])
    token = read_json("files/tokens.json")["debug"]
    bot.run(token)


