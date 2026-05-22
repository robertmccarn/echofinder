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


def _fetch(seed: str) -> dict:
    client = TestClient(api_main.app)
    response = client.get("/api/recommendations", params={"seed": seed})
    if response.status_code == 404:
        body = response.json()
        return {"seed": seed, "error": body.get("error", {}).get("message", "Not found")}
    response.raise_for_status()
    return response.json()


def _format_section(data: dict) -> str:
    if "error" in data:
        return f"  ERROR: {data['error']}\n"

    lines: list[str] = []
    lines.append(f"Seed: {data['seed']}")
    lines.append(f"Reason: {data['metadata']['reason']}")
    lines.append("")
    lines.append("Source Status:")
    for source, status in data["metadata"]["source_status"].items():
        msg = status.get("message", "")
        if msg:
            lines.append(f"  - {source}: {status['status']} ({msg})")
        else:
            lines.append(f"  - {source}: {status['status']}")
    lines.append("")

    sa = data["seed_artist"]
    has_meta = sa.get("image_url") or sa.get("genres") or sa.get("spotify_url")
    if has_meta:
        lines.append("Seed Artist Metadata:")
        if sa.get("image_url"):
            lines.append(f"  Image: {sa['image_url']}")
        if sa.get("genres"):
            lines.append(f"  Genres: {', '.join(sa['genres'])}")
        if sa.get("spotify_url"):
            lines.append(f"  Spotify: {sa['spotify_url']}")
        lines.append("")

    for section, label in [("modern_echoes", "Modern Echoes"), ("bridge_artists", "Bridge Artists")]:
        items = data.get(section, [])
        lines.append(f"{label}:")
        if not items:
            lines.append("  (none)")
        else:
            for i, card in enumerate(items, 1):
                lines.append(f"  {i}. {card['artist_name']}")
                lines.append(f"     Echo Score: {card['echo_score']}")
                lines.append(f"     Confidence: {card['confidence']}")
                lines.append(f"     Emergence: {card['emergence_type']} ({card['emergence_year']})")
                if card.get("shared_tags"):
                    lines.append(f"     Shared Tags: {', '.join(card['shared_tags'][:5])}")
                lines.append(f"     Sources: {', '.join(card['sources'])}")
                if card.get("source_note"):
                    lines.append(f"     Explanation: {card['source_note']}")
                if card.get("spotify_url"):
                    lines.append(f"     Spotify: {card['spotify_url']}")
                if card.get("image_url"):
                    lines.append(f"     Image: {card['image_url']}")
                if card.get("genres"):
                    lines.append(f"     Genres: {', '.join(card['genres'][:5])}")
                lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="EchoFinder Live Demo")
    parser.add_argument("--seed", type=str, help="Single seed artist")
    parser.add_argument("--all", action="store_true", help="Run all canonical seeds")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
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
        return 0

    print("EchoFinder Live Demo")
    print("====================")
    print()

    for i, seed in enumerate(seeds):
        data = _fetch(seed)
        print(_format_section(data))
        if i < len(seeds) - 1:
            print("---")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
