import datetime
import discord
from discord.ext import commands, tasks

from modules.utils import read_json, make_embed_history
from modules.riot_tracker.client import RiotClient
from modules.riot_tracker.storage import JsonStorage
from modules.riot_tracker.chore import add_user_riot, remove_riot_account, get_history, get_new_matches, get_full_data_history
from modules.riot_tracker.lol_basher import bash_user

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

id_file = read_json("files/id_dict.json")

bot = commands.Bot(command_prefix='!', intents=intents)

# === Riot tracker setup ===
RIOT_API_KEY = read_json("files/tokens.json")["riot_key"]

riot_client = RiotClient(api_key=RIOT_API_KEY)
storage = JsonStorage("files/discord_users.json")

# Load existing users from storage
discord_users = storage.load()

# ============================

utc = datetime.timezone.utc
daily_check = datetime.time(hour=2, minute=0, second=0, tzinfo=utc)

async def send_message_to_me(message, is_file=False, is_embed=False):
    user = bot.get_guild(int(id_file["guild_id"])).get_member(int(id_file["my_id"]))
    if user:
        if is_file:
            await user.send(file=message)
        elif is_embed:
            await user.send(embed=message)
        else:
            await user.send(message)
    else:
        print("[Error] Couldn't send message to me")

async def send_message_to_user(message, user_id, is_file=False):
    try:
        user = await bot.fetch_user(int(user_id))
        if is_file:
            await user.send(file=message)
        else:
            await user.send(message)
    except Exception as e:
        user_name = bot.get_user(int(user_id)).name
        print(f"[Error] Couldn't send message to user {user_name} ({user_id}): {e}")

@bot.event
async def on_ready():
    print('Bot is ready to go!')

    if not check_new_matches.is_running():
        check_new_matches.start()

    if not bash_users.is_running():
        bash_users.start()

    await send_message_to_me("I'm online! 🔥")

@tasks.loop(seconds=300)
async def check_new_matches():
    for discord_id in discord_users:
        notifications = get_new_matches(discord_users, discord_id, riot_client)

        storage.save(discord_users)  # saving latest data after the check

        new_matches = [(t, a, d) for (_, t, a, d) in notifications]

        if not new_matches:
            continue

        embed = make_embed_history(new_matches)

        await send_message_to_me(f"New matches detected:")
        await send_message_to_me(embed, is_embed=True)

@tasks.loop(seconds=14400)  # 4 hours
async def bash_users():
    for users in discord_users.values():
        discord_id = users.discord_id
        guild_id = users.guild_id

        history = get_full_data_history(discord_users, riot_client, discord_id)

        user = bot.get_guild(int(guild_id)).get_member(discord_id)
        msg = bash_user(user, history)

        if msg:
            await send_message_to_me(msg)

@bot.command(name="add_user")
async def add_user(ctx, *, args):
    """Add a new Discord user with one Riot account, or add a Riot account to an existing user."""
    splitted_args = args.split(' ')
    if len(splitted_args) != 2:
        await ctx.send("Usage: !add_user <game_name> #<tag_line>")
        return

    discord_id = ctx.author.id
    game_name, tag_line = args.split(' ', 1)
    if not tag_line.startswith('#'):
        await ctx.send("Tag line must start with '#'")
        return
    tag_line = tag_line[1:]  # Remove '#'

    try:
        msg = add_user_riot(storage, riot_client, discord_id, discord_users, game_name, tag_line)
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error adding user: {e}")

@bot.command(name="delete_account")
async def delete_account(ctx, discord_id: int, game_name: str, tag_line: str):
    """Delete a Riot account from a Discord user."""
    try:
        msg = remove_riot_account(storage, discord_id, discord_users, game_name, tag_line)
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error deleting account: {e}")

@bot.command(name="history")
async def history(ctx, last: int = 5):
    """
    Display your recent match history for all saved Riot accounts.
    Shows up to 'last' matches total, sorted by date (newest first).
    """
    discord_id = ctx.author.id

    # Get history using your helper
    try:
        matches, error_msg = get_history(discord_users, riot_client, discord_id, last)
        if matches is None:
            await ctx.send(error_msg)
            return
    except Exception as e:
        await ctx.send(f"Error retrieving history: {e}")
        return

    if not matches:
        await ctx.send("No matches found.")
        return

    embed = make_embed_history(matches)

    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

if __name__ == '__main__':
    token = read_json("files/tokens.json")["debug"]
    my_id = int(id_file["my_id"])
    bot.run(token)
