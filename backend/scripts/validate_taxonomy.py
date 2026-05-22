"""
Validate that tag values in EchoFinder data files conform to the
controlled taxonomy defined in backend/data/tag_taxonomy.json.

Usage:
    python backend/scripts/validate_taxonomy.py

Exits with code 0 if all values are valid, 1 if issues are found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "backend" / "data"


def load_taxonomy() -> dict:
    path = DATA_DIR / "tag_taxonomy.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def check_categorical_values(
    category: str,
    allowed: set[str],
    records: list[dict],
    record_name_key: str,
    field: str,
) -> list[str]:
    errors: list[str] = []
    for rec in records:
        name = rec.get(record_name_key, "unknown")
        values = rec.get(field, [])
        if not isinstance(values, list):
            errors.append(f"  [{category}/{field}] {name}: field is not a list")
            continue
        for val in values:
            if val not in allowed:
                errors.append(
                    f"  [{category}/{field}] {name}: '{val}' not in taxonomy"
                )
    return errors


def main() -> int:
    taxonomy = load_taxonomy()
    allowed_cats = taxonomy.get("categories", {})
    allowed_genres = set(allowed_cats.get("genres", {}).get("allowed_values", []))
    allowed_tones = set(allowed_cats.get("emotional_tones", {}).get("allowed_values", []))
    allowed_themes = set(allowed_cats.get("lyrical_themes", {}).get("allowed_values", []))
    allowed_tags = set(allowed_cats.get("raw_tags", {}).get("allowed_values", []))

    errors: list[str] = []

    # Validate legacy_artists.json
    leg_path = DATA_DIR / "legacy_artists.json"
    if leg_path.exists():
        with leg_path.open(encoding="utf-8") as fh:
            legacy = json.load(fh)
        errors.extend(
            check_categorical_values("legacy", allowed_genres, legacy, "name", "genres")
        )
        errors.extend(
            check_categorical_values("legacy", allowed_tones, legacy, "name", "emotional_tones")
        )
        errors.extend(
            check_categorical_values("legacy", allowed_themes, legacy, "name", "lyrical_themes")
        )
        errors.extend(
            check_categorical_values("legacy", allowed_tags, legacy, "name", "tags")
        )
    else:
        errors.append("  legacy_artists.json not found")

    # Validate modern_candidate_pool.json
    mod_path = DATA_DIR / "modern_candidate_pool.json"
    if mod_path.exists():
        with mod_path.open(encoding="utf-8") as fh:
            modern = json.load(fh)
        errors.extend(
            check_categorical_values("modern_pool", allowed_genres, modern, "name", "genres")
        )
        errors.extend(
            check_categorical_values("modern_pool", allowed_tones, modern, "name", "emotional_tones")
        )
        errors.extend(
            check_categorical_values("modern_pool", allowed_themes, modern, "name", "lyrical_themes")
        )
        errors.extend(
            check_categorical_values("modern_pool", allowed_tags, modern, "name", "tags")
        )
    else:
        errors.append("  modern_candidate_pool.json not found")

    if errors:
        print("Taxonomy validation FAILED:")
        for err in errors:
            print(err)
        return 1
    else:
        print("Taxonomy validation PASSED: all tag values conform to taxonomy.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
