from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


_YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2}|21\d{2})\b")
_MIN_YEAR = 1900


@dataclass(frozen=True)
class EmergenceResolution:
    resolved_year: int | None
    source_field: str | None
    fallback_used: bool
    is_modern_window: bool
    window_start_year: int
    window_end_year: int
    note: str


def _parse_year(value: Any, current_year: int) -> int | None:
    if isinstance(value, int):
        year = value
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            year = int(stripped)
        else:
            match = _YEAR_PATTERN.search(stripped)
            year = int(match.group(1)) if match else None
    else:
        year = None

    if year is None:
        return None
    if year < _MIN_YEAR or year > current_year + 1:
        return None
    return year


def resolve_emergence_year(artist: dict[str, Any], current_year: int, window_years: int = 5) -> EmergenceResolution:
    window_start_year = current_year - window_years
    window_end_year = current_year

    candidate_fields = (
        "first_known_year",
        "emergence_year",
        "debut_year",
        "formed_year",
    )

    for index, field in enumerate(candidate_fields):
        parsed_year = _parse_year(artist.get(field), current_year)
        if parsed_year is not None:
            return EmergenceResolution(
                resolved_year=parsed_year,
                source_field=field,
                fallback_used=index > 0,
                is_modern_window=parsed_year >= window_start_year,
                window_start_year=window_start_year,
                window_end_year=window_end_year,
                note="resolved",
            )

    return EmergenceResolution(
        resolved_year=None,
        source_field=None,
        fallback_used=True,
        is_modern_window=False,
        window_start_year=window_start_year,
        window_end_year=window_end_year,
        note="unresolved_year",
    )
