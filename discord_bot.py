import discord
from utils import is_valid_url, extract_from_url, get_size

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

anniversaries = {}


@client.event
async def on_ready():
    print('Bot is ready to go!')


@client.event
async def on_message(message):
    print(message)
    print("id:", message.id)
    print("channel:", message.channel)
    print("type:", message.type)
    print("author:", message.author)
    print("content:", message.content)

    if not (message.channel == "Direct Message with Unknown User" or "bot" in message.channel):
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

# token = 'MTA4Mjc4MDI2NDQwMjUyMjIyMw.GXuGLV.iXcIubo2aZeME90gAxVm60aNtTZ18pXm6oBhMo'  # Flash_bot
token = 'MTE5MjA4MTgwMDQ4NzUwMTgzNA.G-Cvw5.YVLzVSEjr9mENfLnoKEgr0AIRlPJEoWc8pNiXE'  # Debug_bot
client.run(token)


