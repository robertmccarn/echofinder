"""
Validate that all EchoFinder data files conform to the expected schema
and that field values are consistent with the controlled taxonomy.

Usage:
    python backend/scripts/validate_dataset.py

Exits with code 0 if all data is valid, 1 if issues are found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "backend" / "data"

_LEGACY_REQUIRED: tuple[str, ...] = (
    "id",
    "name",
    "tags",
    "spotify_url",
    "active_years",
    "genres",
    "emotional_tones",
    "lyrical_themes",
    "production_style",
    "vocal_style",
    "scene_lineage",
    "notes",
)

_MODERN_REQUIRED: tuple[str, ...] = (
    "id",
    "name",
    "formed_year",
    "active_status",
    "spotify_url",
    "monthly_listeners",
    "genres",
    "emotional_tones",
    "lyrical_themes",
    "production_style",
    "vocal_style",
    "scene_lineage",
    "curator_notes",
    "recommended_legacy_matches",
)

_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_SPOTIFY_PATTERN = re.compile(
    r"^(https://open\.spotify\.com/artist/[a-zA-Z0-9]+)?$"
)
_MIN_YEAR = 1900
_MAX_FUTURE_YEAR_OFFSET = 2


def load_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        print(f"  {filename}: file not found")
        sys.exit(1)
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_taxonomy() -> dict:
    path = DATA_DIR / "tag_taxonomy.json"
    if not path.exists():
        print("  tag_taxonomy.json: file not found")
        sys.exit(1)
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def check_required_fields(
    records: list[dict],
    required: tuple[str, ...],
    label: str,
    name_key: str = "name",
) -> list[str]:
    errors: list[str] = []
    for i, rec in enumerate(records):
        name = rec.get(name_key, f"record[{i}]")
        for field in required:
            if field not in rec:
                errors.append(f"  [{label}] {name}: missing required field '{field}'")
    return errors


def check_ids(records: list[dict], label: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for rec in records:
        rid = rec.get("id", "")
        name = rec.get("name", rid)
        if not rid:
            errors.append(f"  [{label}] {name}: id is empty")
            continue
        if rid in seen:
            errors.append(f"  [{label}] {name}: duplicate id '{rid}'")
        seen.add(rid)
        if not _ID_PATTERN.match(rid):
            errors.append(
                f"  [{label}] {name}: id '{rid}' does not match expected pattern "
                f"(lowercase, hyphenated)"
            )
    return errors


def check_categorical_values(
    records: list[dict],
    category_name: str,
    allowed: set[str],
    label: str,
    field: str,
    name_key: str = "name",
) -> list[str]:
    errors: list[str] = []
    for rec in records:
        name = rec.get(name_key, "unknown")
        values = rec.get(field, [])
        if not isinstance(values, list):
            errors.append(f"  [{label}/{field}] {name}: field is not a list")
            continue
        for val in values:
            if val not in allowed:
                errors.append(
                    f"  [{label}/{field}] {name}: '{val}' not in taxonomy"
                )
    return errors


def check_urls(records: list[dict], label: str, field: str = "spotify_url") -> list[str]:
    errors: list[str] = []
    for rec in records:
        name = rec.get("name", "unknown")
        url = rec.get(field, "")
        if not isinstance(url, str):
            errors.append(f"  [{label}] {name}: {field} is not a string")
            continue
        if url and not _SPOTIFY_PATTERN.match(url):
            errors.append(
                f"  [{label}] {name}: {field} '{url}' does not match "
                f"expected Spotify URL pattern"
            )
    return errors


def check_modern_years(records: list[dict]) -> list[str]:
    errors: list[str] = []
    current_year = 2026
    for rec in records:
        name = rec.get("name", "unknown")
        formed = rec.get("formed_year")
        if formed is None:
            errors.append(f"  [modern_pool] {name}: formed_year is missing")
            continue
        if not isinstance(formed, int):
            errors.append(f"  [modern_pool] {name}: formed_year is not an integer")
            continue
        if formed < _MIN_YEAR or formed > current_year + _MAX_FUTURE_YEAR_OFFSET:
            errors.append(
                f"  [modern_pool] {name}: formed_year {formed} is out of range"
            )
    return errors


def check_active_status(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for rec in records:
        name = rec.get("name", "unknown")
        status = rec.get("active_status")
        if not isinstance(status, bool):
            errors.append(
                f"  [modern_pool] {name}: active_status should be a boolean, "
                f"got {type(status).__name__}"
            )
    return errors


def check_monthly_listeners(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for rec in records:
        name = rec.get("name", "unknown")
        listeners = rec.get("monthly_listeners")
        if listeners is None:
            errors.append(f"  [modern_pool] {name}: monthly_listeners is missing")
            continue
        if not isinstance(listeners, int) or listeners < 0:
            errors.append(
                f"  [modern_pool] {name}: monthly_listeners should be a "
                f"non-negative integer, got {listeners!r}"
            )
    return errors


def check_backward_compat(records: list[dict]) -> list[str]:
    errors: list[str] = []
    for rec in records:
        name = rec.get("name", "unknown")
        has_old = "related_legacy_styles" in rec
        has_new = "recommended_legacy_matches" in rec
        if not has_new:
            errors.append(
                f"  [modern_pool] {name}: missing recommended_legacy_matches"
            )
        if not has_old:
            errors.append(
                f"  [modern_pool] {name}: missing related_legacy_styles "
                f"(required for backward compat)"
            )
    return errors


def main() -> int:
    taxonomy = load_taxonomy()
    cats = taxonomy.get("categories", {})

    allowed_genres = set(cats.get("genres", {}).get("allowed_values", []))
    allowed_tones = set(cats.get("emotional_tones", {}).get("allowed_values", []))
    allowed_themes = set(cats.get("lyrical_themes", {}).get("allowed_values", []))
    allowed_tags = set(cats.get("raw_tags", {}).get("allowed_values", []))

    errors: list[str] = []

    print("Validating legacy_artists.json ...")
    legacy = load_json("legacy_artists.json")
    errors.extend(check_required_fields(legacy, _LEGACY_REQUIRED, "legacy"))
    errors.extend(check_ids(legacy, "legacy"))
    errors.extend(check_urls(legacy, "legacy"))
    errors.extend(
        check_categorical_values(legacy, "legacy", allowed_genres, "legacy", "genres")
    )
    errors.extend(
        check_categorical_values(
            legacy, "legacy", allowed_tones, "legacy", "emotional_tones"
        )
    )
    errors.extend(
        check_categorical_values(
            legacy, "legacy", allowed_themes, "legacy", "lyrical_themes"
        )
    )
    errors.extend(
        check_categorical_values(legacy, "legacy", allowed_tags, "legacy", "tags")
    )

    print("Validating modern_candidate_pool.json ...")
    modern = load_json("modern_candidate_pool.json")
    errors.extend(check_required_fields(modern, _MODERN_REQUIRED, "modern_pool"))
    errors.extend(check_ids(modern, "modern_pool"))
    errors.extend(check_urls(modern, "modern_pool"))
    errors.extend(check_modern_years(modern))
    errors.extend(check_active_status(modern))
    errors.extend(check_monthly_listeners(modern))
    errors.extend(check_backward_compat(modern))
    errors.extend(
        check_categorical_values(modern, "modern_pool", allowed_genres, "modern_pool", "genres")
    )
    errors.extend(
        check_categorical_values(
            modern, "modern_pool", allowed_tones, "modern_pool", "emotional_tones"
        )
    )
    errors.extend(
        check_categorical_values(
            modern, "modern_pool", allowed_themes, "modern_pool", "lyrical_themes"
        )
    )
    errors.extend(
        check_categorical_values(modern, "modern_pool", allowed_tags, "modern_pool", "tags")
    )

    if errors:
        print("\nDataset validation FAILED:")
        for err in errors:
            print(err)
        return 1
    else:
        print("\nDataset validation PASSED: all data files conform to schema.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
