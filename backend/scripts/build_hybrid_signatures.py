from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.hybrid_service import HybridRuntime
from backend.app.reco_config import load_reco_config


def _load_json(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def run(limit: int | None = None) -> dict[str, int]:
    root = Path(__file__).resolve().parents[2]
    legacy = _load_json(root / "backend" / "data" / "legacy_artists.json")
    modern = _load_json(root / "backend" / "data" / "modern_candidate_pool.json")

    all_records: list[dict] = []
    for row in legacy:
        all_records.append(
            {
                "id": row["id"],
                "name": row["name"],
                "genres": row.get("genres", []),
                "tags": row.get("tags", []),
                "emotional_tones": row.get("emotional_tones", []),
                "lyrical_themes": row.get("lyrical_themes", []),
                "production_style": row.get("production_style", ""),
                "vocal_style": row.get("vocal_style", ""),
                "scene_lineage": row.get("scene_lineage", ""),
                "notes": row.get("notes", ""),
                "first_known_year": None,
                "formed_year": None,
            }
        )
    for row in modern:
        all_records.append(
            {
                "id": row.get("id") or row.get("name", "").strip().casefold().replace(" ", "-"),
                "name": row.get("name", ""),
                "genres": row.get("genres", []),
                "tags": row.get("tags", []),
                "emotional_tones": row.get("emotional_tones", []),
                "lyrical_themes": row.get("lyrical_themes", []),
                "production_style": row.get("production_style", ""),
                "vocal_style": row.get("vocal_style", ""),
                "scene_lineage": row.get("scene_lineage", ""),
                "notes": row.get("curator_notes", ""),
                "first_known_year": row.get("first_known_year"),
                "formed_year": row.get("formed_year"),
                "debut_year": row.get("debut_year"),
                "emergence_year": row.get("emergence_year"),
                "release_count": row.get("release_count", 1),
            }
        )

    if limit is not None:
        all_records = all_records[:limit]

    config = load_reco_config()
    runtime = HybridRuntime.from_config(config)
    if runtime.store is None:
        raise RuntimeError("DATABASE_URL is required for Postgres-backed signature pipeline.")

    for rec in all_records:
        runtime.compute_signature(rec["id"], rec)

    return {"artists_processed": len(all_records)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and persist hybrid signature vectors.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    result = run(limit=args.limit)
    print(json.dumps(result))


if __name__ == "__main__":
    main()

