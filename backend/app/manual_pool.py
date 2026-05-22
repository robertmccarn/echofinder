from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .candidates import CandidateSourceRecord, SourceName, merge_candidate_records

# Stable confidence score for human-curated manual pool matches.
# 0.75 reflects a manual/curated recommendation — not a perfect
# algorithmic certainty but a deliberate human judgment.
DEFAULT_MANUAL_CONFIDENCE: float = 0.75


def _load_raw_pool() -> list[dict]:
    root = Path(__file__).resolve().parents[2]
    path = root / "backend" / "data" / "modern_candidate_pool.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _get_related_styles(entry: dict) -> list[str]:
    return entry.get("recommended_legacy_matches") or entry.get("related_legacy_styles", [])


def is_eligible(entry: dict, seed_name: str) -> bool:
    """Return ``True`` if *entry* is an eligible candidate for *seed_name*.

    Eligibility rules
    -----------------
    * ``name`` must be non-empty.
    * ``active_status`` must not be explicitly ``False``.
    * At least one related legacy style must match *seed_name*
      (case-insensitive, whitespace-insensitive).
    """
    name = entry.get("name", "")
    if not name or not isinstance(name, str):
        return False

    active = entry.get("active_status")
    if active is False:
        return False

    seed_normalized = seed_name.strip().casefold()
    related = _get_related_styles(entry)
    return any(s.strip().casefold() == seed_normalized for s in related)


def entry_to_candidate(entry: dict, seed_name: str) -> CandidateSourceRecord:
    """Convert a raw JSON pool entry into a ``CandidateSourceRecord``."""
    external_urls: dict[str, str] = {}
    spotify = entry.get("spotify_url", "")
    if spotify:
        external_urls["spotify"] = spotify

    return CandidateSourceRecord(
        source_name=SourceName.MANUAL_POOL.value,
        artist_name=entry.get("name", ""),
        related_seed=seed_name,
        confidence_signal=DEFAULT_MANUAL_CONFIDENCE,
        tags=list(entry.get("tags", [])),
        emergence_year=entry.get("emergence_year"),
        first_known_year=entry.get("first_known_year"),
        debut_year=entry.get("debut_year"),
        formed_year=entry.get("formed_year"),
        emotional_tones=list(entry.get("emotional_tones", [])),
        lyrical_themes=list(entry.get("lyrical_themes", [])),
        production_style=entry.get("production_style", ""),
        vocal_style=entry.get("vocal_style", ""),
        scene_lineage=entry.get("scene_lineage", ""),
        match_explanation=entry.get("source_note", ""),
        external_urls=external_urls,
    )


class ManualPoolSource:
    """Candidate source backed by ``modern_candidate_pool.json``.

    Usage
    -----
    .. code-block:: python

        source = ManualPoolSource()
        candidates = source.get_candidates("Manchester Orchestra")
    """

    def __init__(self, pool: list[dict] | None = None):
        """If *pool* is ``None``, load from the default JSON file."""
        self._raw = pool if pool is not None else _load_raw_pool()

    def get_candidates(self, seed_name: str) -> list[CandidateSourceRecord]:
        """Return eligible, deduped candidates for *seed_name*.

        Steps
        -----
        1. Filter the raw pool through :func:`is_eligible`.
        2. Convert each eligible entry to a ``CandidateSourceRecord``.
        3. Group by artist name and run :func:`merge_candidate_records`
           on each group to handle duplicate entries for the same artist.
        """
        eligible = [e for e in self._raw if is_eligible(e, seed_name)]
        records = [entry_to_candidate(e, seed_name) for e in eligible]

        groups: dict[str, list[CandidateSourceRecord]] = {}
        for rec in records:
            key = rec.artist_name.strip().casefold()
            groups.setdefault(key, []).append(rec)

        result: list[CandidateSourceRecord] = []
        for group in groups.values():
            merged = merge_candidate_records(group)
            if merged is not None:
                result.append(merged)
        return result
