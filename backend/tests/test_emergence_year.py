from __future__ import annotations

from backend.app.emergence import resolve_emergence_year


def test_resolve_uses_primary_year_field() -> None:
    artist = {"first_known_year": 2024}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=5)
    assert result.resolved_year == 2024
    assert result.source_field == "first_known_year"
    assert result.is_modern_window is True
    assert result.fallback_used is False


def test_resolve_falls_back_to_secondary_field() -> None:
    artist = {"first_known_year": None, "emergence_year": "2022"}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=5)
    assert result.resolved_year == 2022
    assert result.source_field == "emergence_year"
    assert result.is_modern_window is True
    assert result.fallback_used is True


def test_resolve_parses_year_from_text() -> None:
    artist = {"debut_year": "debuted in 2021 (local scene)"}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=5)
    assert result.resolved_year == 2021
    assert result.source_field == "debut_year"
    assert result.is_modern_window is True


def test_resolve_unresolved_when_no_valid_year() -> None:
    artist = {"first_known_year": "unknown", "emergence_year": 1800}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=5)
    assert result.resolved_year is None
    assert result.source_field is None
    assert result.is_modern_window is False
    assert result.note == "unresolved_year"


def test_modern_window_boundary_inclusive() -> None:
    artist = {"first_known_year": 2021}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=5)
    assert result.window_start_year == 2021
    assert result.is_modern_window is True
