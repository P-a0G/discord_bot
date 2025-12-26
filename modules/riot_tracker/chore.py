from .models import DiscordUser, RiotAccount

REGION = "europe"

def add_user_riot(storage, riot_client, discord_id: int, discord_users, game_name: str, tag_line: str):
    puuid = riot_client.get_puuid(game_name, tag_line)
    msg = "Error: Unknown error occurred."

    if discord_id in discord_users:
        # Add new Riot account to existing user
        account = RiotAccount(game_name=game_name, tag_line=tag_line, region=REGION, puuid=puuid)
        discord_users[discord_id].riot_accounts.append(account)
        msg = f"Added new Riot account {game_name}#{tag_line} to existing user {discord_id}"
    else:
        # Create new user
        account = RiotAccount(game_name=game_name, tag_line=tag_line, region=REGION, puuid=puuid)
        discord_users[discord_id] = DiscordUser(discord_id=discord_id, riot_accounts=[account])
        msg = f"Created new user {discord_id} with Riot account {game_name}#{tag_line}"

    storage.save({uid: user.__dict__ for uid, user in discord_users.items()})

    return msg


def remove_riot_account(storage, discord_id: int, discord_users, game_name: str, tag_line: str):
    if discord_id not in discord_users:
        return f"No user with Discord ID {discord_id}"

    user = discord_users[discord_id]
    before_count = len(user.riot_accounts)
    user.riot_accounts = [acc for acc in user.riot_accounts if not (acc.game_name == game_name and acc.tag_line == tag_line)]

    if len(user.riot_accounts) < before_count:
        storage.save({uid: u.__dict__ for uid, u in discord_users.items()})
        return f"Deleted Riot account {game_name}#{tag_line} from user {discord_id}"
    else:
        return f"Account {game_name}#{tag_line} not found for user {discord_id}"


def get_history(discord_users, riot_client, discord_id: int, last: int = 5):
    if discord_id not in discord_users:
        return None, "You don't have any Riot accounts saved."

    user = discord_users[discord_id]
    if not user.riot_accounts:
        return None, "You don't have any Riot accounts saved."

    all_matches = []

    for account in user.riot_accounts:
        match_ids = riot_client.get_match_ids(account.puuid, count=last)
        for match_id in match_ids:
            match_details = riot_client.get_match_summary(match_id, puuid=account.puuid)
            all_matches.append((match_details['date'], account, match_details))

    # Sort matches by game start time descending
    all_matches.sort(key=lambda x: x[0], reverse=True)

    # Limit to 'last' matches
    all_matches = all_matches[:last]

    return all_matches, None

def get_new_matches(storage, discord_users, discord_id, riot_client):
    user = discord_users.get(discord_id, None)

    if user is None:
        return []

    notifications = []

    for account in user.riot_accounts:
        match_ids = riot_client.get_match_ids(account.puuid, count=10)
        new_matches = [mid for mid in match_ids if mid not in account.seen_matches]

        for match_id in new_matches:
            match_details = riot_client.get_match_summary(match_id, puuid=account.puuid)
            notifications.append((user.discord_id, match_details['date'], account, match_details))
            account.seen_matches.add(match_id)

    storage.save(discord_users)

    return notifications