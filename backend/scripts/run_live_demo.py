"""
Live demo / real-world test for EchoFinder MVP.

Usage:
    python backend/scripts/run_live_demo.py
    python backend/scripts/run_live_demo.py --seed "Manchester Orchestra"
    python backend/scripts/run_live_demo.py --all
    python backend/scripts/run_live_demo.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from backend.app import main as api_main

CANONICAL_SEEDS: list[str] = [
    "Manchester Orchestra",
    "Thrice",
    "The Decemberists",
]
RULE = "=" * 72
SUBRULE = "-" * 72


def _fetch(seed: str) -> dict:
    client = TestClient(api_main.app)
    response = client.get("/api/recommendations", params={"seed": seed})
    if response.status_code == 404:
        body = response.json()
        return {"seed": seed, "error": body.get("error", {}).get("message", "Not found")}
    response.raise_for_status()
    return response.json()


def _format_confidence(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.1%}"
    return str(value)


def _score_to_100(score: object) -> str:
    if isinstance(score, (int, float)):
        # Current API often emits 0-100-ish values; keep output compact.
        return f"{float(score):.1f}"
    return str(score)


def _source_status_line(source: str, status: dict) -> str:
    label = status.get("status", "unknown")
    msg = status.get("message", "")
    if msg:
        return f"- {source}: {label} ({msg})"
    return f"- {source}: {label}"


def _format_card(card: dict, idx: int) -> list[str]:
    lines: list[str] = []
    lines.append(f"[REC {idx}] {card['artist_name']}")
    lines.append(f"  Echo Score: {_score_to_100(card['echo_score'])}")
    lines.append(f"  Confidence: {_format_confidence(card['confidence'])}")
    lines.append(f"  Why it fits: {card.get('source_note', 'No explanation provided.')}")
    lines.append(f"  Emergence: {card['emergence_type']} ({card['emergence_year']})")
    if card.get("shared_tags"):
        lines.append(f"  Shared tags: {', '.join(card['shared_tags'][:6])}")
    if card.get("spotify_url"):
        lines.append(f"  Listen: {card['spotify_url']}")
    if card.get("genres"):
        lines.append(f"  Genres: {', '.join(card['genres'][:4])}")
    return lines


def _format_section(data: dict) -> str:
    if "error" in data:
        return f"Could not generate recommendations for '{data.get('seed', 'Unknown seed')}'.\nReason: {data['error']}\n"

    lines: list[str] = [SUBRULE]
    modern = data.get("modern_echoes", [])
    bridges = data.get("bridge_artists", [])
    lines.append(f"Now Playing From: {data['seed']}")
    lines.append(f"Result signal: {data['metadata']['reason']}")
    lines.append(f"Found {len(modern)} modern echo(es) and {len(bridges)} bridge artist(s).")
    lines.append("")
    lines.append("[SECTION] Data Source Health")
    for source, status in data["metadata"]["source_status"].items():
        lines.append(_source_status_line(source, status))
    lines.append("")

    sa = data["seed_artist"]
    has_meta = sa.get("image_url") or sa.get("genres") or sa.get("spotify_url")
    if has_meta:
        lines.append("[SECTION] Seed Artist")
        if sa.get("image_url"):
            lines.append(f"- Image: {sa['image_url']}")
        if sa.get("genres"):
            lines.append(f"- Genres: {', '.join(sa['genres'])}")
        if sa.get("spotify_url"):
            lines.append(f"- Spotify: {sa['spotify_url']}")
        lines.append("")

    lines.append("[SECTION] Top Picks")
    if modern:
        top = modern[0]
        lines.append(f"- Start with {top['artist_name']} ({_score_to_100(top['echo_score'])})")
        if top.get("spotify_url"):
            lines.append(f"- Quick listen: {top['spotify_url']}")
    else:
        lines.append("- No modern echoes found for immediate listening.")
    lines.append("")

    for section, label in [("modern_echoes", "Modern Echoes"), ("bridge_artists", "Bridge Artists")]:
        items = data.get(section, [])
        lines.append(f"[SECTION] {label}")
        if not items:
            lines.append("- None")
        else:
            for i, card in enumerate(items, 1):
                lines.extend(_format_card(card, i))
                lines.append("")
    lines.append(SUBRULE)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="EchoFinder Live Demo")
    parser.add_argument("--seed", type=str, help="Single seed artist")
    parser.add_argument("--all", action="store_true", help="Run all canonical seeds")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--wait", action="store_true", help="Wait for Enter before exiting")
    args = parser.parse_args()

    if args.seed and args.all:
        parser.error("Use either --seed or --all, not both.")

    if args.seed:
        seeds = [args.seed]
    else:
        seeds = CANONICAL_SEEDS

    if args.json:
        results: dict[str, dict] = {}
        for seed in seeds:
            results[seed] = _fetch(seed)
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        _maybe_wait(args.wait)
        return 0

    print(RULE)
    print("EchoFinder CLI Demo")
    print(RULE)
    print("Goal: help a listener quickly find modern recommendations with clear reasons.")
    print()

    for i, seed in enumerate(seeds):
        data = _fetch(seed)
        print(_format_section(data))
        if i < len(seeds) - 1:
            print("---")
            print()

    _maybe_wait(args.wait)
    return 0


def _maybe_wait(explicit_wait: bool) -> None:
    # Do not block automated test runs.
    if "PYTEST_CURRENT_TEST" in os.environ:
        return

    # Pause if user asked explicitly, or when a shell prompt variable is missing
    # (common when launched by double-click and the window would close immediately).
    should_wait = explicit_wait or "PROMPT" not in os.environ
    if should_wait:
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass


if __name__ == "__main__":
    sys.exit(main())
