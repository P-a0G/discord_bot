import requests
from .queues import QUEUE_ID_TO_NAME



class RiotClient:
    def __init__(self, api_key: str, region: str="europe", platform: str="euw1"):
        self.headers = {"X-Riot-Token": api_key}
        self.region = region
        self.platform = platform

    def get_puuid(self, game_name: str, tag_line: str) -> str:
        url = (
            f"https://{self.region}.api.riotgames.com/"
            f"riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()["puuid"]

    def get_match_ids(self, puuid: str, count: int = 5) -> list[str]:
        url = (
            f"https://{self.region}.api.riotgames.com/"
            f"lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        )
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _extract_summary(self, match: dict, puuid: str) -> dict:
        info = match["info"]
        queue_id = info["queueId"]

        for p in info["participants"]:
            if p["puuid"] == puuid:
                return {
                    "match_id": match["metadata"]["matchId"],
                    "champion": p["championName"],
                    "win": p["win"],
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "assists": p["assists"],
                    "queue": QUEUE_ID_TO_NAME.get(queue_id, "Other"),
                    "duration_min": info["gameDuration"] // 60,
                    "date": info["gameStartTimestamp"],
                }

    def get_match(self, match_id: str, puuid: str) -> dict:
        url = (
            f"https://{self.region}.api.riotgames.com/"
            f"lol/match/v5/matches/{match_id}"
        )
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return self._extract_summary(r.json(), puuid=puuid)
