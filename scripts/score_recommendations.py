"""
Rank EchoFinder recommendations from local backend data.

Usage:
    python scripts/score_recommendations.py
    python scripts/score_recommendations.py --seed "Manchester Orchestra"
    python scripts/score_recommendations.py --all
    python scripts/score_recommendations.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient

from backend.app.main import app

CANONICAL_SEEDS = [
    "Manchester Orchestra",
    "Thrice",
    "The Decemberists",
]


def _fetch(seed: str) -> dict:
    client = TestClient(app)
    response = client.get("/api/recommendations", params={"seed": seed})
    if response.status_code != 200:
        return {"seed": seed, "error": response.text}
    return response.json()


def _rank_cards(data: dict) -> list[dict]:
    cards: list[dict] = []
    for card in data.get("modern_echoes", []):
        card_copy = dict(card)
        card_copy["group"] = "modern_echoes"
        cards.append(card_copy)
    for card in data.get("bridge_artists", []):
        card_copy = dict(card)
        card_copy["group"] = "bridge_artists"
        cards.append(card_copy)
    cards.sort(key=lambda x: float(x.get("echo_score", 0.0)), reverse=True)
    return cards


def _print_seed(seed: str, data: dict) -> None:
    print("=" * 80)
    print(f"Seed: {seed}")
    if "error" in data:
        print(f"ERROR: {data['error']}")
        return

    ranked = _rank_cards(data)
    print(f"Recommendations: {len(ranked)}")
    if len(ranked) < 5:
        print("Note: fewer than 5 recommendations available for this seed in current local data.")
    print(f"Reason: {data.get('metadata', {}).get('reason', '')}")
    print("")

    for i, card in enumerate(ranked, 1):
        print(f"[{i}] {card.get('artist_name', '')} ({card.get('group', '')})")
        print(f"    Echo Score: {card.get('echo_score', '')}")
        print(f"    Emergence Year: {card.get('emergence_year', '')}")
        print(f"    Shared Tags: {', '.join(card.get('shared_tags', [])) or 'None'}")
        print(f"    Sources: {', '.join(card.get('sources', [])) or 'None'}")
        print(f"    Explanation: {card.get('source_note', '') or 'None'}")
        if card.get("spotify_url"):
            print(f"    Spotify: {card.get('spotify_url')}")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank EchoFinder recommendations")
    parser.add_argument("--seed", type=str, help="Single seed artist")
    parser.add_argument("--all", action="store_true", help="Run all canonical seeds")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    if args.seed and args.all:
        parser.error("Use either --seed or --all, not both.")

    seeds = [args.seed] if args.seed else CANONICAL_SEEDS
    result = {}
    for seed in seeds:
        data = _fetch(seed)
        ranked = _rank_cards(data) if "error" not in data else []
        result[seed] = {"raw": data, "ranked": ranked}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0

    print("EchoFinder Ranking Script")
    for seed in seeds:
        _print_seed(seed, result[seed]["raw"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
