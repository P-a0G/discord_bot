import json
from pathlib import Path
from typing import Any, Dict

from modules.riot_tracker.models import DiscordUser, RiotAccount, Channel


class JsonStorage:
    def __init__(self, path: str):
        self.path = Path(path)

    def save(self, data: dict):
        # Convert dataclasses to dict recursively
        serializable_data = self._make_serializable(data)
        self.path.write_text(json.dumps(serializable_data, indent=2))

    def load(self) -> dict[int, "DiscordUser"]:
        """
        Load data from JSON and convert into DiscordUser objects
        with RiotAccount dataclasses. Returns a dict keyed by discord_id.
        """
        if not self.path.exists():
            return {}

        raw_data = json.loads(self.path.read_text())
        users = {}

        for uid, data in raw_data.items():
            riot_accounts = []
            for acc_data in data.get("riot_accounts", []):
                # Convert seen_matches back to set
                acc_data["seen_matches"] = set(acc_data.get("seen_matches", []))
                riot_accounts.append(RiotAccount(**acc_data))

            users[int(uid)] = DiscordUser(
                discord_id=int(uid),
                guild_id=data.get("guild_id", 0),
                riot_accounts=riot_accounts
            )

        return users

    def _make_serializable(self, obj: Any):
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, set):
            return list(obj)  # Convert sets to lists
        elif hasattr(obj, "__dict__"):
            return {k: self._make_serializable(v) for k, v in obj.__dict__.items()}
        else:
            return obj


class JsonChannelStorage:
    def __init__(self, path: str):
        self.path = Path(path)

    def save(self, channels: Dict[int, Channel]):
        """
        Save channels to JSON.
        Expects a dict keyed by guild_id.
        """
        serializable_data = {
            str(guild_id): {
                "guild_id": channel.guild_id,
                "channel_id": channel.channel_id,
            }
            for guild_id, channel in channels.items()
        }

        self.path.write_text(json.dumps(serializable_data, indent=2))

    def load(self) -> Dict[int, Channel]:
        """
        Load channels from JSON.
        Returns a dict keyed by guild_id.
        """
        if not self.path.exists():
            return {}

        raw_data = json.loads(self.path.read_text())
        channels = {}

        for guild_id, data in raw_data.items():
            channels[int(guild_id)] = Channel(
                guild_id=data["guild_id"],
                channel_id=data["channel_id"],
            )

        return channels
