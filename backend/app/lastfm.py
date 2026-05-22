from __future__ import annotations

import os

import requests


class LastFmClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @classmethod
    def from_env(cls) -> LastFmClient | None:
        api_key = os.environ.get("LASTFM_API_KEY")
        if not api_key:
            return None
        return cls(api_key)

    def search_artist_exists(self, name: str) -> bool:
        resp = requests.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "artist.search",
                "artist": name,
                "api_key": self._api_key,
                "format": "json",
                "limit": 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        body = resp.json()
        matches = (
            body.get("results", {})
            .get("artistmatches", {})
            .get("artist", [])
        )
        if isinstance(matches, dict):
            return True
        return bool(matches)
