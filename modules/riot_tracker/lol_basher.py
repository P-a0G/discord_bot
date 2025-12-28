import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .message_templates import TEMPLATES
from .queues import QUEUE_ID_TO_NAME

# ============================================================
# Types
# ============================================================

MatchTuple = Tuple[str, Dict[str, Any]]
ParsedMatch = Dict[str, Any]

FOUR_HOURS = 4


# ============================================================
# Time helpers
# ============================================================

def _safe_get_match_timestamp(match: Dict[str, Any]) -> Optional[datetime]:
    try:
        ms = match.get("info", {}).get("gameStartTimestamp")
        if not ms:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except Exception:
        return None


def filter_recent_matches(history: Iterable[MatchTuple], hours: int):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [
        (puuid, match)
        for puuid, match in history or []
        if _safe_get_match_timestamp(match)
        and _safe_get_match_timestamp(match) >= cutoff
    ]


# ============================================================
# Parsing
# ============================================================

def _compute_kda(k: int, d: int, a: int) -> float:
    return round((k + a) / max(1, d), 2)


def parse_participant_entry(puuid: str, match: Dict[str, Any]) -> Optional[ParsedMatch]:
    try:
        participants = match["info"]["participants"]
        queue_id = match["info"]["queueId"]
        team_kills = sum(p["kills"] for p in participants[:5])  # Assuming first 5 = team
        team_deaths = sum(p["deaths"] for p in participants[:5])
        team_assists = sum(p["assists"] for p in participants[:5])

        enemy_kills = sum(p["kills"] for p in participants[5:])
        enemy_deaths = sum(p["deaths"] for p in participants[5:])
        enemy_assists = sum(p["assists"] for p in participants[5:])

        for p in participants:
            if p["puuid"] == puuid:
                return {
                    "timestamp": _safe_get_match_timestamp(match),
                    "win": p["win"],
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "assists": p["assists"],
                    "kda_ratio": _compute_kda(p["kills"], p["deaths"], p["assists"]),
                    "champion": p["championName"],
                    "damage": p["totalDamageDealtToChampions"],
                    "team_kills": team_kills,
                    "team_deaths": team_deaths,
                    "team_assists": team_assists,
                    "enemy_kills": enemy_kills,
                    "enemy_deaths": enemy_deaths,
                    "enemy_assists": enemy_assists,
                    "queue_id": queue_id,
                    "queue": QUEUE_ID_TO_NAME[queue_id]
                }
    except Exception:
        pass
    return None


def build_parsed_history(history: Iterable[MatchTuple]) -> List[ParsedMatch]:
    parsed = []
    for puuid, match in history:
        p = parse_participant_entry(puuid, match)
        if p:
            parsed.append(p)
    parsed.sort(key=lambda x: x["timestamp"])
    return parsed


# ============================================================
# Analysis
# ============================================================

def detect_recent_streak(matches: List[ParsedMatch]):
    if not matches:
        return None, 0

    last_match = matches[-1]
    last_win = last_match["win"]
    last_queue_type = last_match.get("queue_id", -1)
    count = 0

    for m in reversed(matches):
        if m["win"] == last_win:
            if m.get("queue_id", -1) == last_queue_type:
                count += 1
            else:
                continue
        else:
            break

    return ("win" if last_win else "lose"), count


def analyze_last_game(matches: List[ParsedMatch]):
    last = matches[-1]

    # Player info
    player = last
    team_total_kills = last["team_kills"]
    player_contrib_ratio = (player["kills"] + player["assists"]) / max(1, team_total_kills)

    # Team and enemy stats
    participants = last.get("raw_participants")  # optional if full participant data is saved
    if not participants:
        # fallback: minimal data from last match
        participants = [
            {
                "puuid": "player",
                "championName": last["champion"],
                "kills": last["kills"],
                "deaths": last["deaths"],
                "assists": last["assists"],
                "win": last["win"],
            }
        ]

    # Split team and enemies by win status
    team = [p for p in participants if p.get("win") == last["win"]]
    enemies = [p for p in participants if p.get("win") != last["win"]]

    # Helper functions
    def best_player(players):
        if not players:
            return None
        p = max(players, key=lambda x: x["kills"] + x["assists"] - x["deaths"])
        return {
            "name": p.get("puuid"),
            "champion": p.get("championName"),
            "score": f"{p['kills']}/{p['deaths']}/{p['assists']}"
        }

    def worst_player(players):
        if not players:
            return None
        p = min(players, key=lambda x: x["kills"] + x["assists"] - x["deaths"])
        return {
            "name": p.get("puuid"),
            "champion": p.get("championName"),
            "score": f"{p['kills']}/{p['deaths']}/{p['assists']}"
        }

    # Best/worst players
    best_team = best_player(team)
    worst_team = worst_player(team)
    best_enemy = best_player(enemies)
    worst_enemy = worst_player(enemies)

    # Return full analysis
    return {
        "last": last,
        "big_win": last["win"] and player["kda_ratio"] >= 8 and player_contrib_ratio > 0.8,
        "big_loss": not last["win"] and player["kda_ratio"] <= 0.4,
        "high_kda": player["kda_ratio"] >= 10,
        "low_kda_but_win": player["kda_ratio"] <= 0.8 and last["win"],
        "carried_but_lost": player["kda_ratio"] >= 7 and not last["win"],
        "player_carried_team": player_contrib_ratio > 0.5 and last["win"],
        "player_carried_by_team": player_contrib_ratio < 0.15 and last["win"],
        "team_crushed": last["win"] and last["team_kills"] > last["enemy_kills"] * 2,
        "team_lost_hard": not last["win"] and last["team_kills"] < last["enemy_kills"] / 2,
        "best_team_player": best_team,
        "worst_team_player": worst_team,
        "best_enemy_player": best_enemy,
        "worst_enemy_player": worst_enemy,
        "very high damage": player["damage"] > 100_000
    }



# ============================================================
# Message Generator
# ============================================================

def _format_template(template_key: str, mention: str, last: ParsedMatch, events: dict, streak_len: int) -> str:
    """
    Generic formatter for TEMPLATES using player's own champion and optional best/worst player info.
    """
    best_team = events.get("best_team_player")
    worst_team = events.get("worst_team_player")
    best_enemy = events.get("best_enemy_player")
    worst_enemy = events.get("worst_enemy_player")

    # Build placeholder dict
    placeholders = {
        "mention": mention,
        "player_champ": last.get("champion", "???"),
        "k": last.get("kills", 0),
        "d": last.get("deaths", 0),
        "a": last.get("assists", 0),
        "kda": last.get("kda_ratio", 0),
        "streak_len": streak_len,
        "best_team_champ": best_team.get("champion") if best_team else "???",
        "best_team_score": best_team.get("score") if best_team else "???",
        "worst_team_champ": worst_team.get("champion") if worst_team else "???",
        "worst_team_score": worst_team.get("score") if worst_team else "???",
        "best_enemy_champ": best_enemy.get("champion") if best_enemy else "???",
        "best_enemy_score": best_enemy.get("score") if best_enemy else "???",
        "worst_enemy_champ": worst_enemy.get("champion") if worst_enemy else "???",
        "worst_enemy_score": worst_enemy.get("score") if worst_enemy else "???",
    }

    template = random.choice(TEMPLATES[template_key])
    return template.format(**placeholders)



def generate_message(mention: str, matches: List[ParsedMatch]) -> str:
    streak_type, streak_len = detect_recent_streak(matches)
    events = analyze_last_game(matches)
    last = events["last"]

    # Prioritize streaks
    if streak_len >= 3:
        key = "win_streak" if streak_type == "win" else "lose_streak"
        return _format_template(key, mention, last, events, streak_len)

    # Map event keys to template keys
    event_template_map = {
        "big_win": "big_win",
        "player_carried_team": "big_win",
        "player_carried_by_team": "low_kda_but_win",
        "team_crushed": "big_win",
        "team_lost_hard": "big_loss",
        "high_kda": "low_kda_but_win",
        "low_kda_but_win": "low_kda_but_win",
        "carried_but_lost": "carried_but_lost",
        "big_loss": "carried_but_lost",
    }

    for event_key, template_key in event_template_map.items():
        if events.get(event_key):
            return _format_template(template_key, mention, last, events, streak_len)

    # Default fallback
    return ""  # no message for default win or lose


# ============================================================
# Public API
# ============================================================

def bash_user(discord_user, history: Optional[Iterable[MatchTuple]]) -> Optional[str]:
    if not history:
        return None

    recent = filter_recent_matches(history, FOUR_HOURS)

    if not recent:
        return None  # no new games → no message

    parsed = build_parsed_history(recent)
    if not parsed:
        return None

    return generate_message(discord_user.mention, parsed)
