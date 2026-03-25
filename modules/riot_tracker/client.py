import threading
import time
from collections import deque

import requests

from .queues import QUEUE_ID_TO_NAME


class RateLimiter:
    """Thread-safe sliding-window rate limiter supporting multiple limit buckets."""

    def __init__(self, limits: list[tuple[int, float]]) -> None:
        # limits: list of (max_requests, window_seconds)
        self._limits = limits
        self._timestamps: list[deque] = [deque() for _ in limits]
        self._lock = threading.Lock()

    def wait(self) -> None:
        """Block until a request can safely be sent according to all buckets."""
        while True:
            with self._lock:
                now = time.monotonic()
                sleep_needed = 0.0

                for i, (max_req, window) in enumerate(self._limits):
                    dq = self._timestamps[i]
                    while dq and now - dq[0] >= window:
                        dq.popleft()

                    if len(dq) >= max_req:
                        wait_until = dq[0] + window + 0.05
                        sleep_needed = max(sleep_needed, wait_until - now)

                if sleep_needed <= 0:
                    # Slot is free: record the request atomically and return
                    now = time.monotonic()
                    for dq in self._timestamps:
                        dq.append(now)
                    return

            # Sleep outside the lock so other threads can check concurrently
            print(f"[RateLimiter] Waiting {sleep_needed:.2f}s to respect API limits...")
            time.sleep(sleep_needed)


class RiotClient:
    # Personal API key limits: 20 req/s and 100 req/2 min
    _RATE_LIMITS: list[tuple[int, float]] = [(20, 1.0), (100, 120.0)]

    def __init__(self, api_key: str, region: str = "europe", platform: str = "euw1") -> None:
        self.headers = {"X-Riot-Token": api_key}
        self.region = region
        self.platform = platform
        self._rate_limiter = RateLimiter(self._RATE_LIMITS)

    def _make_request(self, url: str) -> dict:
        """Make a rate-limited GET request, retrying automatically on 429."""
        while True:
            self._rate_limiter.wait()
            r = requests.get(url, headers=self.headers)
            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", 5))
                print(f"[RateLimiter] 429 received, retrying after {retry_after}s...")
                time.sleep(retry_after + 1)
                continue
            r.raise_for_status()
            return r.json()

    def get_puuid(self, game_name: str, tag_line: str) -> str:
        url = (
            f"https://{self.region}.api.riotgames.com/"
            f"riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        return self._make_request(url)["puuid"]

    def get_match_ids(self, puuid: str, count: int = 5) -> list[str]:
        url = (
            f"https://{self.region}.api.riotgames.com/"
            f"lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
        )
        return self._make_request(url)

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

    def get_match(self, match_id: str) -> dict:
        url = (
            f"https://{self.region}.api.riotgames.com/"
            f"lol/match/v5/matches/{match_id}"
        )
        return self._make_request(url)

    def get_match_summary(self, match_id: str, puuid: str) -> dict:
        return self._extract_summary(self.get_match(match_id), puuid)
