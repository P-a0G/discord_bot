import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
        for p in match["info"]["participants"]:
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

    last_win = matches[-1]["win"]
    count = 0

    for m in reversed(matches):
        if m["win"] == last_win:
            count += 1
        else:
            break

    return ("win" if last_win else "lose"), count


def analyze_last_game(matches: List[ParsedMatch]):
    last = matches[-1]
    return {
        "last": last,
        "big_win": last["win"] and last["damage"] >= 25000,
        "big_loss": not last["win"] and last["deaths"] >= 10,
        "high_kda": last["kda_ratio"] >= 4,
        "low_kda_but_win": last["kda_ratio"] <= 1 and last["win"],
        "carried_but_lost": last["kda_ratio"] >= 3 and not last["win"],
    }


# ============================================================
# Templates
# ============================================================

TEMPLATES = {
    "lose_streak": [
        "{mention}, série de {n} défaites. Respire, prends une pause, et arrête de blâmer le ping.",
        "{mention}, {n} défaites à la suite. Tes coéquipiers demandent des excuses publiques.",
        "{mention}, tu tombes sur une mauvaise série ({n}). On tente la roulette ou on switch de rôle ?",
        "{mention}, {n} défaites… la seule chose que tu carries c'est la tristesse.",
        "{mention}, {n} losses de suite… ça devient épique, mais pas dans le bon sens.",
        "{mention}, encore une défaite ({n})… les adversaires doivent t'envoyer des fleurs.",
        "{mention}, {n} défaites, bientôt un Guinness pour la série la plus tragique ?",
        "{mention}, série négative ({n}) — la seule chose stable ici c'est ton malheur.",
        "{mention}, {n} losses consécutives. On devrait ouvrir un fan club de tes défaites ?",
    ],
    "big_loss": [
        "{mention}, game catastrophique : {k}/{d}/{a} avec {d} morts. Besoin de play safe ou d'un verre d'eau ?",
        "{mention}, ça a mal tourné sur {champ}. Peut-être que le remake était trop tard.",
        "{mention}, {k}/{d}/{a}… je n'ai même pas de mots, sauf RIP.",
        "{mention}, {champ} t'a trahi, ou tu as trahi {champ} ?",
        "{mention}, quel désastre ! Même tes coéquipiers ont pleuré en voyant {k}/{d}/{a}.",
        "{mention}, impressionnant… mais dans le mauvais sens ({k}/{d}/{a}).",
        "{mention}, si la défaite était un art, tu serais Picasso ({k}/{d}/{a}).",
    ],
    "default_lose": [
        "{mention}, mauvaise game — remets-toi et reviens plus fort.",
        "{mention}, on déclare tribunal sur ces coéquipiers, ou on reset le mmr ?",
        "{mention}, ça arrive… respire et retry.",
        "{mention}, défaite classique, mais avec style ({k}/{d}/{a}) ?",
        "{mention}, encore raté… peut-être qu'une sieste était nécessaire avant la partie.",
        "{mention}, la game est perdue, mais ton ego survit encore.",
        "{mention}, échec critique… mais au moins tu as tenté.",
    ],
    "carried_but_lost": [
        "{mention}, tu as tenté de porter avec {k}/{d}/{a} mais la team n'a pas suivi. Rage sur les autres, pas sur toi.",
        "{mention}, performance individuelle top ({k}/{d}/{a}) mais scoreboard dit non. Tragédie grecque.",
        "{mention}, tu brilles mais la team coule le navire.",
        "{mention}, MVP de la défaite, ça se fête quand même ({k}/{d}/{a}).",
        "{mention}, tu as été l'exception dans un monde de chaos.",
    ],
    "win_streak": [
        "{mention}, série de {n} victoires — t'es en feu, arrête de porter les autres comme ça.",
        "{mention}, {n} wins de suite. Tu veux un peu d'humilité ou tu veux qu'on proclame MVP ?",
        "{mention}, {n} victoires d'affilée. Respire, champion — l'ego va exploser.",
        "{mention}, {n} wins ! Les adversaires doivent pleurer en silence.",
        "{mention}, {n} victoires d'affilée… tu triches ou quoi ?",
        "{mention}, encore un win… bientôt tu demanderas une statue à ton nom.",
        "{mention}, {n} victoires consécutives. Les ennemis se suicident juste en te voyant.",
    ],
    "big_win": [
        "{mention}, énorme game sur {champ} ({k}/{d}/{a}, KDA {kda}) — les adversaires ont déjà demandé pardon.",
        "{mention}, tu as explosé la partie avec {champ} — même les bots ont peur.",
        "{mention}, performance divine ! {champ} n'a jamais été aussi OP ({k}/{d}/{a}).",
        "{mention}, tu carries tellement que les ennemis veulent te bannir IRL.",
        "{mention}, victoire écrasante avec {champ} — trop facile pour toi.",
    ],
    "low_kda_but_win": [
        "{mention}, victoire chanceuse ({k}/{d}/{a}) — tu devrais remercier tes mates.",
        "{mention}, tu gagnes malgré {k}/{d}/{a}… la chance est avec toi, pas le skill.",
        "{mention}, victoire improbable ! Tu es le roi des ratés heureux ({k}/{d}/{a}).",
        "{mention}, tu as gagné sans briller ({k}/{d}/{a})… c'est presque un art.",
    ],
    "default_win": [
        "{mention}, bonne game — mais ne t'emballe pas trop.",
        "{mention}, clean win, tu ne vas pas me surprendre la prochaine fois ?",
        "{mention}, victoire tranquille, les adversaires ont laissé faire.",
        "{mention}, tu gagnes encore… quand arrêtes-tu de les écraser ?",
        "{mention}, pas mal, mais le vrai challenge arrive bientôt.",
    ],
}

# ============================================================
# Message Generator
# ============================================================

def generate_message(mention: str, matches: List[ParsedMatch]) -> str:
    streak_type, streak_len = detect_recent_streak(matches)
    events = analyze_last_game(matches)
    last = events["last"]

    if streak_len >= 2:
        key = "win_streak" if streak_type == "win" else "lose_streak"
        return random.choice(TEMPLATES[key]).format(
            mention=mention, n=streak_len
        )

    if events["big_win"]:
        return random.choice(TEMPLATES["big_win"]).format(
            mention=mention, champ=last["champion"],
            k=last["kills"], d=last["deaths"], a=last["assists"],
            kda=last["kda_ratio"]
        )

    if events["high_kda"]:
        return random.choice(TEMPLATES["big_win"]).format(
            mention=mention, champ=last["champion"],
            k=last["kills"], d=last["deaths"], a=last["assists"],
            kda=last["kda_ratio"]
        )

    if events["low_kda_but_win"]:
        return random.choice(TEMPLATES["low_kda_but_win"]).format(
            mention=mention, k=last["kills"], d=last["deaths"], a=last["assists"]
        )

    if events["carried_but_lost"]:
        return random.choice(TEMPLATES["carried_but_lost"]).format(
            mention=mention, k=last["kills"], d=last["deaths"], a=last["assists"]
        )

    if events["big_loss"]:
        return random.choice(TEMPLATES["big_loss"]).format(
            mention=mention, champ=last["champion"],
            k=last["kills"], d=last["deaths"], a=last["assists"]
        )

    return random.choice(
        TEMPLATES["default_win" if last["win"] else "default_lose"]
    ).format(mention=mention)


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
