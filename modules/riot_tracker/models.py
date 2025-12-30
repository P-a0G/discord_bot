from dataclasses import dataclass, field
from typing import List


@dataclass
class RiotAccount:
    game_name: str
    tag_line: str
    region: str
    puuid: str
    latest_match_seen_date: int = 0


@dataclass
class DiscordUser:
    discord_id: int
    guild_id: int
    riot_accounts: List[RiotAccount] = field(default_factory=list)


@dataclass
class Channel:
    guild_id: int
    channel_id: int
