from __future__ import annotations

import os

import requests


class MusicBrainzClient:
    def __init__(self, user_agent: str) -> None:
        self._user_agent = user_agent

    @classmethod
    def from_env(cls) -> MusicBrainzClient | None:
        user_agent = os.environ.get("MUSICBRAINZ_USER_AGENT")
        if not user_agent:
            return None
        return cls(user_agent)

    def search_artist_exists(self, name: str) -> bool:
        resp = requests.get(
            "https://musicbrainz.org/ws/2/artist/",
            params={"query": f"artist:{name}", "fmt": "json", "limit": 1},
            headers={"User-Agent": self._user_agent},
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        return bool(body.get("artists", []))
