from __future__ import annotations

import json

import pytest

from backend.scripts import run_live_demo


def _ok_payload(seed: str) -> dict:
    return {
        "seed": seed,
        "seed_artist": {
            "id": seed.lower().replace(" ", "-"),
            "name": seed,
            "spotify_url": "",
            "image_url": "",
            "genres": [],
        },
        "modern_echoes": [
            {
                "artist_name": "Modern Example",
                "classification": "modern_echo",
                "echo_score": 0.77,
                "confidence": "high",
                "emergence_type": "modern",
                "emergence_year": 2023,
                "shared_tags": ["emo", "indie rock"],
                "sources": ["manual_pool"],
                "source_note": "Strong overlap in tone and structure.",
                "spotify_url": "",
                "image_url": "",
                "genres": [],
            }
        ],
        "bridge_artists": [
            {
                "artist_name": "Bridge Example",
                "classification": "bridge_artist",
                "echo_score": 0.61,
                "confidence": "medium",
                "emergence_type": "bridge",
                "emergence_year": 2012,
                "shared_tags": ["alt rock"],
                "sources": ["manual_pool"],
                "source_note": "Explains lineage from seed to modern echoes.",
                "spotify_url": "",
                "image_url": "",
                "genres": [],
            }
        ],
        "metadata": {
            "reason": "results_found",
            "source_status": {
                "manual_pool": {"status": "ok", "message": ""},
                "lastfm_graph": {"status": "planned", "message": "Not implemented in manual MVP"},
                "musicbrainz": {"status": "planned", "message": "Not implemented in manual MVP"},
                "spotify": {"status": "unavailable", "message": "Spotify credentials not configured"},
            },
        },
    }


def test_live_demo_default_runs_canonical_seeds(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(run_live_demo, "_fetch", lambda seed: _ok_payload(seed))
    monkeypatch.setattr("sys.argv", ["run_live_demo.py"])

    code = run_live_demo.main()
    output = capsys.readouterr().out

    assert code == 0
    for seed in run_live_demo.CANONICAL_SEEDS:
        assert f"Seed: {seed}" in output
    assert "Modern Echoes:" in output
    assert "Bridge Artists:" in output
    assert "Explanation:" in output
    assert "Source Status:" in output


def test_live_demo_single_seed(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(run_live_demo, "_fetch", lambda seed: _ok_payload(seed))
    monkeypatch.setattr("sys.argv", ["run_live_demo.py", "--seed", "Manchester Orchestra"])

    code = run_live_demo.main()
    output = capsys.readouterr().out

    assert code == 0
    assert "Seed: Manchester Orchestra" in output
    assert "Seed: Thrice" not in output
    assert "Seed: The Decemberists" not in output


def test_live_demo_json_mode(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(run_live_demo, "_fetch", lambda seed: _ok_payload(seed))
    monkeypatch.setattr("sys.argv", ["run_live_demo.py", "--all", "--json"])

    code = run_live_demo.main()
    output = capsys.readouterr().out

    assert code == 0
    body = json.loads(output)
    assert set(body.keys()) == set(run_live_demo.CANONICAL_SEEDS)
    assert body["Manchester Orchestra"]["metadata"]["source_status"]["manual_pool"]["status"] == "ok"


def test_live_demo_unknown_seed_shows_error_reason(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        run_live_demo,
        "_fetch",
        lambda seed: {"seed": seed, "error": f"Unknown seed '{seed}'"},
    )
    monkeypatch.setattr("sys.argv", ["run_live_demo.py", "--seed", "Unknown Artist"])

    code = run_live_demo.main()
    output = capsys.readouterr().out

    assert code == 0
    assert "ERROR: Unknown seed 'Unknown Artist'" in output


def test_live_demo_seed_and_all_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["run_live_demo.py", "--seed", "Thrice", "--all"])
    with pytest.raises(SystemExit):
        run_live_demo.main()
