from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class RiotAccount:
    game_name: str
    tag_line: str
    region: str
    puuid: str
    seen_matches: Set[str] = field(default_factory=set)


@dataclass
class DiscordUser:
    discord_id: int
    riot_accounts: List[RiotAccount] = field(default_factory=list)
