import discord
from discord.ext import commands
from modules.utils import read_json, is_valid_url, get_size
from modules.music_utils import extract_from_url

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

id_file = read_json("files/id_dict.json")

bot = commands.Bot(command_prefix='!', intents=intents)

subscribed_to_music = dict()


@bot.event
async def on_ready():
    print('Bot is ready to go!')

    # if not test_loop.is_running():
    #     test_loop.start()


@bot.command(name='set')
async def set_music_dict(ctx):
    if (ctx.guild.id, ctx.author.id) not in subscribed_to_music.keys():
        subscribed_to_music[(ctx.guild.id, ctx.author.id)] = []

        user = bot.get_guild(ctx.guild.id).get_member(ctx.author.id)

        await user.send("Music set done")


async def send_message_to_me(message):
    for guild_id, user_id in subscribed_to_music.keys():
        if user_id == int(id_file["my_id"]) and guild_id == int(id_file["guild_id"]):
            user = bot.get_guild(guild_id).get_member(user_id)

            await user.send(message)
        else:
            print("[Error] Couldn't send mp to me")


async def send_message_to_sub(message):
    for guild_id, user_id in subscribed_to_music.keys():
        user = bot.get_guild(guild_id).get_member(user_id)

        await user.send(message)


@bot.event
async def on_message(message):
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    show_message_info(message)

    if not (str(message.channel) == "Direct Message with Unknown User" or "bot" in str(message.channel)):
        return

    if message.author == bot.user:
        return

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


if __name__ == '__main__':
    # token = read_json("files/tokens.json")["Flash_bot"]
    token = read_json("files/tokens.json")["debug"]
    bot.run(token)


