import datetime
import os
import random
from collections import defaultdict

import discord
from discord.ext import commands, tasks

from modules.utils import read_json, write_json  # , show_message_info

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

utc = datetime.timezone.utc
time_birthday_check = datetime.time(hour=8, minute=0, second=0, tzinfo=utc)

anniversary_dict_path = "files/anniversary.json"
if os.path.exists(anniversary_dict_path):
    anniversaries = read_json(anniversary_dict_path)
else:
    anniversaries = dict()


@bot.event
async def on_ready():
    print('Bot is ready to go!')
    if not birthday_check.is_running():
        birthday_check.start()

    await send_message_to_me("I'm online!")


@tasks.loop(time=time_birthday_check)
async def birthday_check():
    today = datetime.date.today()

    # Iterate through registered birthdays
    for guild_id in anniversaries.keys():
        for user_id_or_name, birthday_date in anniversaries[guild_id].items():
            # Check if it's the user's birthday
            if today.day == birthday_date["day"] and today.month == birthday_date["mounth"]:
                try:
                    user_id_or_name = int(user_id_or_name)
                    user = bot.get_guild(int(guild_id)).get_member(user_id_or_name)
                except Exception:
                    user = None

                if user:
                    print(f"\t\tIt's {user.name} Birthday ! 🎉🎂")
                    channel_id = int(id_file["birthday_channel_id"][guild_id])
                    channel = bot.get_guild(int(guild_id)).get_channel(channel_id)
                    await channel.send(get_birthday_message(user))
                else:
                    print(f"\t\tIt's {user_id_or_name} Birthday ! 🎉🎂")
                    await send_message_to_me(f"It's {user_id_or_name} Birthday ! 🎉🎂")


def get_birthday_message(user):
    with open('files/birthday_messages.txt', 'r', encoding='utf-8') as file:
        messages = file.readlines()
    return random.choice(messages).strip().format(user=user)


async def send_message_to_me(message):
    user = bot.get_guild(my_guild_id).get_member(my_id)
    if user:
        await user.send(message)
    else:
        print("[Error] Couldn't send mp to me")


@bot.command(name='set_birthday', help='Register your birthday')
async def register_birthday(ctx, birthday_date, user=None):
    if len(birthday_date.split("/")) == 2:
        day, mounth = birthday_date.split("/")
        year = None
    elif len(birthday_date.split("/")) == 3:
        day, mounth, year = birthday_date.split("/")
        year = int(year)
    else:
        await ctx.send("Format invalide, utiliser: '!set birthday DD/MM/YYYY'.")
        return
    day = int(day)
    mounth = int(mounth)

    try:
        if year is None:
            datetime.datetime(2000, mounth, day)
        else:
            datetime.datetime(year, mounth, day)
    except Exception:
        await ctx.send("Date incorrecte, utiliser: '!set birthday DD/MM/YYYY'.")
        return

    if ctx.author.id == my_id:
        if user is None:
            user = str(ctx.author.id)
    else:
        if user is not None:  # enregistrement perso pour les mp
            return
        user = str(ctx.author.id)

    if ctx.guild is not None:
        print(f"Save birthday: guild={ctx.guild.id} user={user}, date={day}/{mounth}/{year}")
        guild_id = str(ctx.guild.id)
    else:
        print(f"Save birthday: user={user}, date={day}/{mounth}/{year}")
        await ctx.send(f"Save birthday: user={user}, date={day}/{mounth}/{year}")
        guild_id = "0"

    if guild_id not in anniversaries.keys():
        anniversaries[guild_id] = {}

    anniversaries[guild_id][user] = {
        "day": day,
        "mounth": mounth
    }
    if year is not None:
        anniversaries[guild_id][user]["year"] = year

    write_json(anniversary_dict_path, anniversaries)

    if guild_id == "0":
        return

    with open('files/birthday_register.txt', 'r', encoding='utf-8') as file:
        messages = file.readlines()
    message = random.choice(messages).strip().format(user=user)
    await ctx.send(message)


@bot.command(name='show_all', help='Register your birthday')
async def show_all(ctx):
    if ctx.author.id != my_id:
        return

    today = datetime.date.today()
    grouped = defaultdict(list)

    for guild_id in anniversaries.keys():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            continue

        for user_id_or_name, birthday in anniversaries[guild_id].items():
            try:
                day = int(birthday["day"])
                month = int(birthday["mounth"])
            except (KeyError, ValueError):
                continue

            # Compute next birthday
            next_birthday = datetime.date(today.year, month, day)
            if next_birthday < today:
                next_birthday = datetime.date(today.year + 1, month, day)

            # Resolve display name
            try:
                member = guild.get_member(int(user_id_or_name))
                name = member.name if member else user_id_or_name
            except Exception:
                name = user_id_or_name

            grouped[month].append((next_birthday, name, day))

    # Sort months chronologically starting from current month
    ordered_months = sorted(grouped.keys(),
                            key=lambda m: (m < today.month, m))

    for month in ordered_months:
        # Sort users inside the month
        grouped[month].sort(key=lambda x: x[0])

        await ctx.send(f"\n📅 **{datetime.date(2000, month, 1).strftime('%B')}**")

        for next_date, name, day in grouped[month]:
            if next_date == today:
                await ctx.send(f"🎉 **{name} — TODAY! ({day}/{month})**")
            else:
                await ctx.send(f"• {name}: {day}/{month}")


@bot.event
async def on_message(message):
    if message.content.startswith("!"):
        await bot.process_commands(message)
    # show_message_info(message)


if __name__ == '__main__':
    id_file = read_json("files/id_dict.json")
    my_id = int(id_file["my_id"])
    token = read_json("files/tokens.json")["birthday_bot"]
    my_guild_id = int(id_file["guild_id"])
    # todo set birthday wish channel with a command

    bot.run(token)
