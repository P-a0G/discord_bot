import datetime
import os
import random

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
    return random.choice([
        f"Joyeux anniversaire, {user.mention} champion(e) du monde de la naissance! 🎉🏆 Que cette journée soit aussi épique que toi! @everyone",
        f"Bon anniversaire, {user.mention} ! 🎂 Aujourd'hui, tu es la vedette, alors fais briller tes bougies comme une star! ✨🕯️ @everyone",
        f"Hé {user.mention}, joyeux anniversaire! 🎉 Espérons que tu reçoives plus de cadeaux que de notifications Facebook aujourd'hui! 🎁📱 @everyone",
        f"Bonne fête, {user.mention}! 🥳 Aujourd'hui, tu es officiellement plus âgé(e), mais ça ne compte pas tant que tu es toujours jeune d'esprit! 🧓➡️👶 @everyone",
        f"Joyeux anniversaire, {user.mention}! 🎈 N'oublie pas que vieillir est obligatoire, mais grandir est facultatif! 🎉🎂 @everyone",
        f"Bon anniv, {user.mention}! 🎉 Souviens-toi, plus tu vieillis, plus tu deviens un classique vintage! 🚗🍷 @everyone",
        f"Hé {user.mention}, c'est ta journée spéciale! 🎂 Profite-en pour manger autant de gâteau que possible sans culpabilité! 🍰😋 @everyone",
        f"Joyeux anniversaire, {user.mention}! 🎊 Si tu étais une bougie, tu éclairerais toute la planète avec ta brillance! 🌍✨ @everyone",
        f"Bon anniversaire, superhéros/superhéroïne {user.mention}! 🎉 Aujourd'hui, tu as le pouvoir de faire ce que tu veux (tant que c'est amusant)! 💪😄 @everyone",
        f"Hé p'tit(e) chanceux(se) {user.mention}, joyeux anniversaire! 🎂 Que la journée soit aussi géniale que toi et remplie de rires contagieux! 😄🎈 @everyone",
        f"C'est le grand jour, {user.mention}! Joyeux anniversaire, notre source préférée de bonne humeur! 🎉🌈 @everyone",
        f"Joyeux anniversaire, {user.mention}! On t'aime plus que le gâteau d'anniversaire lui-même! 🎂💖 @everyone",
        f"Bonne fête, {user.mention}! Aujourd'hui, tu es la rockstar de la fête! 🤘🎸 @everyone",
        f"Hé {user.mention}, joyeux anniversaire! On espère que ta journée est aussi incroyable que toi! 🚀😄 @everyone",
        f"Bon anniversaire, {user.mention}! Que la force de la joie soit avec toi aujourd'hui! 🌟😄 @everyone",
        f"Hé toi, {user.mention}! Joyeux anniversaire! On te décerne la médaille d'honneur de la bonne humeur! 🏅😊 @everyone",
        f"Bonne fête, {user.mention}! Aujourd'hui, tu es le chef de la fête, alors profite bien de ton règne! 🎉👑 @everyone",
        f"Joyeux anniversaire, {user.mention}! Que ta journée soit aussi pétillante que du champagne! 🍾✨ @everyone",
        f"Bon anniversaire, {user.mention}! Souviens-toi, tu n'es pas vieux, tu es classique! 🎉🎩 @everyone",
        f"Hé {user.mention}, c'est ton jour! Joyeux anniversaire! On espère que tu reçois plus de câlins que de cadeaux! 🤗🎁 @everyone",
        f"Bonne fête, {user.mention}! Aujourd'hui, tu es la star, alors brille aussi fort que les étoiles! 🌠😊 @everyone",
        f"Joyeux anniversaire, {user.mention}! On te souhaite une journée remplie de rires et de moments inoubliables! 😄🎈 @everyone",
        f"Bon anniversaire, {user.mention}! Que cette année soit pleine de surprises aussi géniales que toi! 🎁🎉 @everyone",
        f"Hé {user.mention}, c'est le moment de faire la fête! Joyeux anniversaire! 🥳🎂 @everyone",
        f"Bonne fête, {user.mention}! Que la magie de ton anniversaire opère et t'apporte bonheur et sourires! ✨😄 @everyone",
        f"Joyeux anniversaire, {user.mention}! On espère que ta journée est aussi exceptionnelle que toi! 🌟🎉 @everyone",
        f"Bon anniversaire, {user.mention}! Profite bien de chaque instant et que cette journée te réserve des surprises incroyables! 🎊😊 @everyone",
        f"Hé toi, {user.mention}! C'est le moment de célébrer! Joyeux anniversaire! 🎉🥂 @everyone",
        f"Bonne fête, {user.mention}! Que cette année t'apporte encore plus de rires et de succès! 😄🎂 @everyone",
        f"Joyeux anniversaire, {user.mention}! On te souhaite une année pleine de moments joyeux et de nouvelles aventures! 🎉🌟 @everyone"
    ])


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
    if ctx.author.id != my_id:
        return

    for guild_id in anniversaries.keys():
        for user_id_or_name, birthday_date in anniversaries[guild_id].items():
            try:
                user = bot.get_guild(int(guild_id)).get_member(int(user_id_or_name))
            except Exception:
                user = None

            if user:
                await ctx.send(f"\t{user.name}: {birthday_date['day']}/{birthday_date['mounth']}")
            else:
                await ctx.send(f"\t{user_id_or_name}: {birthday_date['day']}/{birthday_date['mounth']}")


@bot.event
async def on_message(message):
    if message.content.startswith("!"):
        print(" > ", message.content)
        await bot.process_commands(message)
    # show_message_info(message)


if __name__ == '__main__':
    id_file = read_json("files/id_dict.json")
    my_id = int(id_file["my_id"])
    token = read_json("files/tokens.json")["birthday_bot"]
    my_guild_id = int(id_file["guild_id"])
    # todo set birthday wish channel with a command

    bot.run(token)
