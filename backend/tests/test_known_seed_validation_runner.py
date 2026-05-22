from __future__ import annotations

import json

from backend.scripts import validate_known_seeds


def _payload(seed: str, modern_count: int) -> dict:
    modern = []
    for idx in range(modern_count):
        modern.append(
            {
                "artist_name": f"{seed} Modern {idx}",
                "classification": "modern_echo",
                "echo_score": 42.0,
                "confidence": 0.4,
                "emergence_type": "first_known_recent",
                "emergence_year": 2022,
                "emergence_resolution": {
                    "source_field": "first_known_year",
                    "fallback_used": False,
                    "is_modern_window": True,
                    "window_start_year": 2021,
                    "window_end_year": 2026,
                    "note": "resolved",
                },
                "shared_tags": ["indie rock"],
                "shared_tag_weights": [{"tag": "indie rock", "weight": 1.0}],
                "component_scores": {
                    "emotional_match": 0.1,
                    "scene_match": 0.1,
                    "lyrical_match": 0.1,
                    "production_match": 0.1,
                    "vocal_match": 0.1,
                    "emerging_bonus": 1.0,
                },
                "sources": ["manual_pool"],
                "source_note": "note",
                "spotify_url": "",
                "image_url": "",
                "genres": [],
            }
        )

    return {
        "seed": seed,
        "seed_artist": {
            "id": seed.lower().replace(" ", "-"),
            "name": seed,
            "spotify_url": "",
            "image_url": "",
            "genres": [],
        },
        "modern_echoes": modern,
        "bridge_artists": [],
        "metadata": {
            "reason": "ok",
            "source_status": {
                "manual_pool": {"status": "ok", "message": ""},
                "lastfm_graph": {"status": "planned", "message": ""},
                "musicbrainz": {"status": "planned", "message": ""},
                "spotify": {"status": "unavailable", "message": ""},
            },
        },
    }


def test_validate_known_seeds_passes_with_recommendations(monkeypatch, tmp_path, capsys) -> None:
    dataset = {
        "credential_groups": {"spotify": ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"]},
        "cases": [
            {
                "seed": "Manchester Orchestra",
                "require_response_schema": True,
                "require_any_recommendations": True,
                "require_non_empty_modern_if_credentials": "spotify",
            }
        ],
    }
    dataset_path = tmp_path / "known_seed_validation_set.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
    monkeypatch.setattr(validate_known_seeds, "DATASET_PATH", dataset_path)

    class _Resp:
        status_code = 200

        def json(self) -> dict:
            return _payload("Manchester Orchestra", modern_count=1)

    class _Client:
        def get(self, *_args, **_kwargs):
            return _Resp()

    monkeypatch.setattr(validate_known_seeds, "TestClient", lambda _app: _Client())
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "x")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "y")

    assert validate_known_seeds.main() == 0
    out = capsys.readouterr().out
    assert "[PASS] Manchester Orchestra" in out
    assert "PASSED" in out


def test_validate_known_seeds_fails_when_credentials_require_non_empty_modern(
    monkeypatch, tmp_path, capsys
) -> None:
    dataset = {
        "credential_groups": {"spotify": ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"]},
        "cases": [
            {
                "seed": "Manchester Orchestra",
                "require_response_schema": True,
                "require_any_recommendations": True,
                "require_non_empty_modern_if_credentials": "spotify",
            }
        ],
    }
    dataset_path = tmp_path / "known_seed_validation_set.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
    monkeypatch.setattr(validate_known_seeds, "DATASET_PATH", dataset_path)

    class _Resp:
        status_code = 200

        def json(self) -> dict:
            return _payload("Manchester Orchestra", modern_count=0)

    class _Client:
        def get(self, *_args, **_kwargs):
            return _Resp()

    monkeypatch.setattr(validate_known_seeds, "TestClient", lambda _app: _Client())
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "x")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "y")

    assert validate_known_seeds.main() == 1
    out = capsys.readouterr().out
    assert "[FAIL] Manchester Orchestra" in out
    assert "non-empty modern_echoes" in out
