from __future__ import annotations

import os

import requests
from pydantic import BaseModel, Field


class SpotifyArtistMetadata(BaseModel):
    name: str
    spotify_url: str = ""
    image_url: str = ""
    genres: list[str] = Field(default_factory=list)


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None

    @classmethod
    def from_env(cls) -> SpotifyClient | None:
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        if not client_id or not client_secret:
            return None
        return cls(client_id, client_secret)

    def _ensure_token(self) -> str:
        if self._token is not None:
            return self._token
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(self._client_id, self._client_secret),
            timeout=10,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def search_artist(self, name: str) -> SpotifyArtistMetadata | None:
        token = self._ensure_token()
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            params={"q": name, "type": "artist", "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        body = resp.json()
        artists = body.get("artists", {}).get("items", [])
        if not artists:
            return None
        artist = artists[0]
        images = artist.get("images", [])
        image_url = images[0]["url"] if images else ""
        return SpotifyArtistMetadata(
            name=artist.get("name", name),
            spotify_url=artist.get("external_urls", {}).get("spotify", ""),
            image_url=image_url,
            genres=artist.get("genres", []),
        )
