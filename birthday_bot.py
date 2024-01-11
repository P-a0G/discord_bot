import os
import discord
from discord.ext import commands, tasks
from utils import read_json, write_json
import datetime
import random


# todo faire une classe bot
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


@tasks.loop(time=time_birthday_check)
async def birthday_check():
    today = datetime.date.today()

    # Iterate through registered birthdays
    for guild_id in anniversaries.keys():
        for user_id_or_name, birthday_date in anniversaries[guild_id].items():
            # Check if it's the user's birthday
            if today.day == birthday_date["day"] and today.month == birthday_date["mounth"]:
                user = bot.get_guild(guild_id).get_member(user_id_or_name)

                if user:
                    print(f"\t\tIt's {user.name} Birthday ! 🎉🎂")
                    channel = bot.get_guild(guild_id).get_channel(int(id_file["birthday_channel_id"]))
                    await channel.send(f"Bon Anniv' {user.mention}! 🎉🎂")
                else:
                    print(f"\t\tIt's {user_id_or_name} Birthday ! 🎉🎂")
                    await send_message_to_me(f"It's {user_id_or_name} Birthday ! 🎉🎂")


async def send_message_to_me(message):
    user = bot.get_guild(my_guild_id).get_member(my_id)
    if user:
        await user.send(message)
    else:
        print("[Error] Couldn't send mp to me")


@bot.command(name='set_birthday', help='Register your birthday')
async def register_birthday(ctx, birthday_date, user=None):
    try:
        if len(birthday_date.split("/")) == 3:
            day, mounth, year = birthday_date.split("/")
            year = int(year)
        else:
            day, mounth = birthday_date.split("/")
            year = None
        day = int(day)
        mounth = int(mounth)

    except ValueError:
        await ctx.send("Format invalide, utiliser: '!set birthday DD/MM/YYYY User'.")
        return

    try:
        datetime.datetime(year, mounth, day)
    except:
        await ctx.send("Date incorrecte, utiliser: '!set birthday DD/MM/YYYY User'.")
        return

    if ctx.author.id != my_id:
        if user is not None:
            return
        else:
            user = ctx.author.id

    print(f"Save birthday: guild={ctx.guild.id} user={user}, date={day}/{mounth}/{year}")

    if ctx.guild.id not in anniversaries.keys():
        anniversaries[ctx.guild.id] = {}

    anniversaries[ctx.guild.id][user] = {
        "day": day,
        "mounth": mounth
    }
    if year is not None:
        anniversaries[user]["year"] = year

    write_json(anniversary_dict_path, anniversaries)
    message = random.choice(
        [
            "Félicitations ! 🎉 Tu as officiellement marqué ta place dans le calendrier ! 📅",
            "Youpi ! 🎈 Ton anniversaire est maintenant verrouillé et chargé ! 🔒",
            "Boom ! 💥 Date d'anniversaire enregistrée ! Prépare-toi pour le train de la fête ! 🚂🎂",
            "Hourra ! 🎊 Tu as jeté ton chapeau d'anniversaire dans l'arène ! 🎩",
            "Attache-toi, copain d'anniversaire ! 🎁 Ta journée spéciale est maintenant sur le radar ! 🛫",
            "Regarde qui vient de devenir la star du spectacle d'anniversaire ! 🌟🎂",
            "Tiens-toi prêt pour une déferlante de vœux d'anniversaire ! 🌊🎉",
            "Ding dong ! 🔔 Date d'anniversaire confirmée et prête à être célébrée ! 🎈",
            "Devine quoi ? 🤔 Tu viens de confirmer ta présence au meilleur jour de tous ! 🎉",
            "Bien joué ! 🏆 Tu as officiellement gagné une place sur la liste VIP d'anniversaire ! 🎂",
            "Tiens-toi bien ! 🤠 Tu viens de t'embarquer dans les montagnes russes de l'excitation d'anniversaire ! 🎢",
            "Ta-da ! 🎩✨ Ta date d'anniversaire fait désormais partie de la programmation magique de la célébration ! 🎉",
            "Oh la la ! 👏 Ton enregistrement d'anniversaire est une raison de faire pleuvoir les confettis ! 🎊🎉",
            "High five ! 🖐️ Tu viens de débloquer l'exploit de l'anticipation d'anniversaire ! 🎮",
            "Bingo ! 🎯 Ton anniversaire est officiellement inscrit sur le calendrier de l'extraordinaire ! 📆",
            "Eh bien, bien, bien ! 🤓 La date d'anniversaire a été consignée dans les archives du plaisir ! 📜",
            "Un tonnerre d'applaudissements ! 👏 Ton anniversaire vient de rejoindre les rangs des célébrations légendaires ! 🎂",
            "Mission accomplie ! 🚀 Ton anniversaire est désormais sur le radar des festivités épiques ! 🎉",
            "Attends voir ! 📞 Tu viens de sécuriser ta place dans le hall de la renommée des anniversaires ! 🏆🎈",
            "Sainte guacamole ! 🥑 Ton enregistrement d'anniversaire vient de lancer la fiesta de l'année ! 🎉💃"
        ]
    )
    await ctx.send(message)


@bot.command(name='show_all', help='Register your birthday')
async def show_all(ctx):
    for guild_id in anniversaries.keys():
        for user_id_or_name, birthday_date in anniversaries[guild_id].items():
            user = bot.get_guild(my_guild_id).get_member(user_id_or_name)

            if user:
                await ctx.send(f"\t{user.name}: {birthday_date['day']}/{birthday_date['mounth']}")
            else:
                await ctx.send(f"\t{user_id_or_name}: {birthday_date['day']}/{birthday_date['mounth']}")


if __name__ == '__main__':
    id_file = read_json("files/id_dict.json")
    my_id = int(id_file["my_id"])
    token = read_json("files/tokens.json")["birthday_bot"]
    my_guild_id = int(id_file["guild_id"])
    birthday_channel_id = int(id_file["birthday_channel_id"])  # todo set channel with a command

    bot.run(token)
