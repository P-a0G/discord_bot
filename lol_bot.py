import asyncio
import datetime

import discord
from discord.ext import commands, tasks

from modules.riot_tracker.chore import (
    add_user_riot,
    remove_riot_account,
    remove_all_riot_accounts,
    get_history,
    get_new_matches,
    get_full_data_history,
    add_channel_lol_bot
)
from modules.riot_tracker.client import RiotClient
from modules.riot_tracker.lol_basher import bash_user
from modules.riot_tracker.storage import JsonStorage, JsonChannelStorage
from modules.utils import read_json, make_embed_history

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

id_file = read_json("files/id_dict.json")

bot = commands.Bot(command_prefix='!', intents=intents)

# === Riot tracker setup ===
RIOT_API_KEY = read_json("files/tokens.json")["riot_key"]

riot_client = RiotClient(api_key=RIOT_API_KEY)
storage = JsonStorage("files/discord_users.json")
channels_storage = JsonChannelStorage("files/lol_bot_channels.json")

# Load existing users from storage
discord_users = storage.load()
channels = channels_storage.load()

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

TIME_TO_CHECK_ONE_USER = 10  # seconds, estimated time to check one user for new matches
SAFE_LOOP_INTERVAL = max(300, len(discord_users) * TIME_TO_CHECK_ONE_USER * 2)  # at least 5 minutes, or more if many users
@bot.event
async def on_ready():
    print('Bot is ready to go!')

    if not check_new_matches.is_running():
        check_new_matches.start()

    await send_message_to_me(f"I'm online! 🍄\n"
                             f"Parameters:\n"
                             f"- safe loop interval: {SAFE_LOOP_INTERVAL}s\n"
                             f"- nb user registered: {len(discord_users)}")

@tasks.loop(seconds=SAFE_LOOP_INTERVAL)
async def check_new_matches() -> None:
    print(f"Starting new match check loop at {datetime.datetime.now()} (interval: {SAFE_LOOP_INTERVAL}s)")
    try:
        await _run_match_check()
    except Exception as e:
        import traceback
        print(f"[Error] Unhandled exception in check_new_matches: {e}")
        traceback.print_exc()


@check_new_matches.error
async def check_new_matches_error(error: Exception) -> None:
    import traceback
    print(f"[Error] check_new_matches task crashed: {error}")
    traceback.print_exc()


async def _run_match_check() -> None:
    for discord_id, discord_user in discord_users.items():
        print("Checking new matches for user ID:", discord_id)
        # Check new matches
        try:
            notifications = get_new_matches(discord_users, discord_id, riot_client)
        except Exception as e:
            print(f"[Error] Failed to get new matches for user ID {discord_id}: {e}")
            continue
        storage.save(discord_users)  # save after checking

        new_matches = [(t, a, d) for (_, t, a, d) in notifications]
        if not new_matches:
            print("No new matches for user ID:", discord_id)
            continue

        # Build embed for notifications
        embed = make_embed_history(new_matches)
        await send_message_to_me(embed, is_embed=True)

        # Get full history
        history = get_full_data_history(discord_users, riot_client, discord_id)
        print(f"Full history for user ID {discord_id} has {len(history)} matches.")

        # Collect all channels this user is registered in
        user_channels = [
            channel for channel in channels.values()
            if channel.guild_id in [g.id for g in bot.guilds]  # make sure guild exists
        ]

        # Find the first channel where this user is present
        stored_msg = False
        msg = ""
        for channel_info in user_channels:
            guild = bot.get_guild(int(channel_info.guild_id))
            if guild is None:
                print("[Warning] Guild not found for channel info:", channel_info)
                continue

            member = guild.get_member(discord_id)
            if member is None:
                print("[Warning] Member not found in guild for user ID:", discord_id)
                continue

            # Only send **one message per user**
            if not stored_msg:
                msg = bash_user(member, discord_user, history)
                stored_msg = True
                print(f"Built message for user {member.name} ({discord_id}): {msg}")
            if msg:
                channel_obj = guild.get_channel(channel_info.channel_id)
                if channel_obj:
                    await channel_obj.send(msg)
                    await send_message_to_me(f"msg: {msg} to user {member.name}")



@bot.command(name="add_user",
             help="Add a new Discord user with one Riot account, or add a Riot account to an existing user. Usage: !add_user <game_name>#<tag_line>")
async def add_user(ctx, *, args: str):
    """Add a new Discord user with one Riot account, or add a Riot account to an existing user."""

    # Riot IDs must contain exactly one '#'
    if "#" not in args:
        await ctx.send("Usage: !add_user <game_name>#<tag_line>")
        return

    game_name, tag_line = args.rsplit("#", 1)

    game_name = game_name.strip()
    tag_line = tag_line.strip()

    if not game_name or not tag_line:
        await ctx.send("Usage: !add_user <game_name>#<tag_line>")
        return

    discord_id = ctx.author.id

    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    guild_id = ctx.guild.id

    try:
        msg = add_user_riot(
            storage,
            riot_client,
            discord_id,
            guild_id,
            discord_users,
            game_name,
            tag_line,
        )
        await ctx.send(msg)

    except Exception as e:
        await ctx.send(f"Error adding user: {e}")


@bot.command(name="delete_user",
             help="Delete a linked Riot account from your profile. Usage: !delete_account <game_name>#<tag_line> or `all`")
async def delete_account(ctx, *, args: str):
    discord_id = ctx.author.id

    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    if args.lower().strip() == "all":
        # confirmation
        await ctx.send(
            "⚠️ This will delete **all** your Riot accounts.\n"
            "Type `confirm` to proceed."
        )

        def check(m):
            return (
                    m.author == ctx.author
                    and m.channel == ctx.channel
                    and m.content.lower() == "confirm"
            )

        try:
            await bot.wait_for("message", check=check, timeout=20)
        except asyncio.TimeoutError:
            await ctx.send("❌ Cancelled.")
            return

        msg = remove_all_riot_accounts(storage, discord_id, discord_users)
        await ctx.send(msg)
        return

    # single account deletion
    if "#" not in args:
        await ctx.send("Usage: !delete_account <game_name>#<tag_line> or `all`")
        return

    game_name, tag_line = args.rsplit("#", 1)
    game_name = game_name.strip()
    tag_line = tag_line.strip()

    if not game_name or not tag_line:
        await ctx.send("Usage: !delete_account <game_name>#<tag_line>")
        return

    try:
        msg = remove_riot_account(
            storage,
            discord_id,
            discord_users,
            game_name,
            tag_line,
        )
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error deleting account: {e}")


@bot.command(name="history",
             help="Display your recent match history for all saved Riot accounts. Usage: !history [last]")
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


@bot.command(name="setup_channel",
             help="Set up the current channel to receive match notifications. Usage: !setup_channel")
async def setup_channel(ctx):
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id

    try:
        msg = add_channel_lol_bot(channels_storage, channels, guild_id, channel_id)
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error adding channel: {e}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

if __name__ == '__main__':
    token = read_json("files/tokens.json")["lol_bot"]
    my_id = int(id_file["my_id"])
    bot.run(token)
