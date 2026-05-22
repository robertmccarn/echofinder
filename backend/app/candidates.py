from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class SourceName(str, Enum):
    """Known candidate sources and their integration status.

    active  - candidate source is integrated in recommendation generation
    planned - candidate source contract is defined but not active for recommendation generation
    """

    MANUAL_POOL = "manual_pool"
    LASTFM_GRAPH = "lastfm_graph"
    MUSICBRAINZ = "musicbrainz"
    SPOTIFY = "spotify"


class CandidateSourceRecord(BaseModel):
    """Contract: every candidate source must produce this record.

    Fields common to all source types. Sources are expected to populate
    as many fields as they can; consumers of this record should handle
    missing data (defaults / None) gracefully.

    ``source_name`` - a ``SourceName`` enum value for single-source
    records, or a ``/``-joined composite (e.g. ``"lastfm_graph/musicbrainz"``)
    after merging.
    """

    source_name: str
    artist_name: str
    related_seed: str
    confidence_signal: float = 0.0
    tags: list[str] = []
    emergence_year: int | None = None
    first_known_year: int | None = None
    debut_year: int | None = None
    formed_year: int | None = None
    emotional_tones: list[str] = []
    lyrical_themes: list[str] = []
    production_style: str = ""
    vocal_style: str = ""
    scene_lineage: str = ""
    match_explanation: str = ""
    external_urls: dict[str, str] = {}


def _pick_longest(a: str, b: str) -> str:
    return a if len(a) >= len(b) else b


def _pick_first_not_none(a: int | None, b: int | None) -> int | None:
    return a if a is not None else b


def merge_candidate_records(records: list[CandidateSourceRecord]) -> CandidateSourceRecord | None:
    """Dedupe-and-merge multiple records for the same artist.

    All input records **must** share the same ``artist_name``
    (comparison is ``strip().casefold()``).  Passing records for
    two or more different artists raises ``ValueError``.

    Rules
    -----
    * Dedup key is ``artist_name`` after ``strip().casefold()``.
    * Tags are unioned (after normalizing — just set union here; consumers
      may further normalise).
    * ``confidence_signal`` takes the **maximum** across records.
    * Year fields (``emergence_year``, ``first_known_year``, etc.) take
      the first non-|None| value encountered.
    * Text fields (``production_style``, ``vocal_style``, etc.) take the
      longer value.
    * ``external_urls`` are merged (later records overwrite same-key
      URLs).
    * ``match_explanation`` is concatenated with ``; `` separator.
    * ``source_name`` is sorted and joined with ``/``.
    """
    if not records:
        return None

    normalized_names = {r.artist_name.strip().casefold() for r in records}
    if len(normalized_names) > 1:
        unique = sorted(normalized_names)
        raise ValueError(
            f"merge_candidate_records requires all records to share the same artist; "
            f"got {len(unique)} distinct normalized names: {unique}"
        )

    keyed: dict[str, list[CandidateSourceRecord]] = {}
    for rec in records:
        key = rec.artist_name.strip().casefold()
        keyed.setdefault(key, []).append(rec)

    merged: list[CandidateSourceRecord] = []
    for group in keyed.values():
        base = group[0]
        sources: set[str] = {base.source_name}
        tags: set[str] = set(base.tags)
        urls: dict[str, str] = dict(base.external_urls)
        explanations: list[str] = (
            [base.match_explanation] if base.match_explanation else []
        )

        max_confidence = base.confidence_signal
        first_emergence = base.emergence_year
        first_first_known = base.first_known_year
        first_debut = base.debut_year
        first_formed = base.formed_year
        best_emotional = base.emotional_tones[:]
        best_lyrical = base.lyrical_themes[:]
        best_production = base.production_style
        best_vocal = base.vocal_style
        best_scene = base.scene_lineage

        for rec in group[1:]:
            sources.add(rec.source_name)
            tags.update(rec.tags)
            urls.update(rec.external_urls)

            if rec.match_explanation:
                explanations.append(rec.match_explanation)

            if rec.confidence_signal > max_confidence:
                max_confidence = rec.confidence_signal

            first_emergence = _pick_first_not_none(
                first_emergence, rec.emergence_year
            )
            first_first_known = _pick_first_not_none(
                first_first_known, rec.first_known_year
            )
            first_debut = _pick_first_not_none(first_debut, rec.debut_year)
            first_formed = _pick_first_not_none(first_formed, rec.formed_year)

            best_production = _pick_longest(best_production, rec.production_style)
            best_vocal = _pick_longest(best_vocal, rec.vocal_style)
            best_scene = _pick_longest(best_scene, rec.scene_lineage)

            if len(rec.emotional_tones) > len(best_emotional):
                best_emotional = rec.emotional_tones[:]
            if len(rec.lyrical_themes) > len(best_lyrical):
                best_lyrical = rec.lyrical_themes[:]

        merged.append(
            CandidateSourceRecord(
                source_name="/".join(sorted(sources)),
                artist_name=group[0].artist_name,
                related_seed=group[0].related_seed,
                confidence_signal=max_confidence,
                tags=sorted(tags),
                emergence_year=first_emergence,
                first_known_year=first_first_known,
                debut_year=first_debut,
                formed_year=first_formed,
                emotional_tones=best_emotional,
                lyrical_themes=best_lyrical,
                production_style=best_production,
                vocal_style=best_vocal,
                scene_lineage=best_scene,
                match_explanation="; ".join(explanations),
                external_urls=urls,
            )
        )

    return merged[0]


def source_status(source: SourceName) -> str:
    """Return the integration status of a source."""
    status_map: dict[SourceName, str] = {
        SourceName.MANUAL_POOL: "active",
        SourceName.LASTFM_GRAPH: "planned",
        SourceName.MUSICBRAINZ: "planned",
        SourceName.SPOTIFY: "planned",
    }
    return status_map.get(source, "unknown")


def all_source_statuses() -> dict[str, str]:
    """Return all known sources and their status, for transparency."""
    return {s.value: source_status(s) for s in SourceName}

