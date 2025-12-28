from dataclasses import dataclass, field
from typing import List


@dataclass
class RiotAccount:
    game_name: str
    tag_line: str
    region: str
    puuid: str
    seen_matches: List[str] = field(default_factory=list)


@dataclass
class DiscordUser:
    discord_id: int
    guild_id: int
    riot_accounts: List[RiotAccount] = field(default_factory=list)


@dataclass
class Channel:
    guild_id: int
    channel_id: int
