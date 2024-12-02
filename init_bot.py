import json
import os
from datetime import datetime


def get_user_input(prompt):
    """Helper function to get user input."""
    return input(prompt).strip()


def ensure_directory(path):
    """Ensure the parent directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def create_id_dict():
    """Create id_dict.json by asking for guild_id and my_id."""
    print("\nCreating id_dict.json...")
    guild_id = get_user_input("Enter the Discord server guild ID: ")
    my_id = get_user_input("Enter your Discord user ID: ")
    data = {"guild_id": guild_id, "my_id": my_id}

    path = "files/id_dict.json"
    ensure_directory(path)
    with open(path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Saved: {path}")


def create_last_update():
    """Create last_update.txt with the current date."""
    print("\nCreating last_update.txt...")
    path = "files/last_update.txt"
    ensure_directory(path)
    with open(path, "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d"))
    print(f"Saved: {path}")


def create_subscribed_artists():
    """Create an empty subscribed_artists.txt."""
    print("\nCreating subscribed_artists.txt...")
    path = "files/subscribed_artists.txt"
    ensure_directory(path)
    open(path, "w").close()  # Creates an empty file
    print(f"Saved: {path}")


def create_tokens():
    """Create tokens.json by asking for API keys."""
    print("\nCreating tokens.json...")
    discord_token = get_user_input("Enter your Discord bot API token: ")
    google_api_key = get_user_input("Enter your Google API key: ")
    data = {
        "Flash_bot": discord_token,
        "google": google_api_key,
    }

    path = "files/tokens.json"
    ensure_directory(path)
    with open(path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Saved: {path}")


def main():
    print("Initializing bot setup...")
    create_id_dict()
    create_last_update()
    create_subscribed_artists()
    create_tokens()
    print("\nInitialization complete! Your bot is ready to start.")


if __name__ == "__main__":
    main()
