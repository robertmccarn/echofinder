from backend.app.emergence import (
    EmergenceResolution,
    compute_emergence_type,
    resolve_emergence_year,
)


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


def test_outside_window_is_not_modern() -> None:
    artist = {"first_known_year": 2015}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=5)
    assert result.is_modern_window is False
    assert result.resolved_year == 2015


def test_custom_window_size() -> None:
    artist = {"first_known_year": 2021}
    result = resolve_emergence_year(artist=artist, current_year=2026, window_years=3)
    assert result.window_start_year == 2023
    assert result.is_modern_window is False


# --- emergence_type tests ---


def _make_emergence(
    source_field: str | None = None,
    is_modern_window: bool = False,
    resolved_year: int | None = 2022,
    note: str = "resolved",
) -> EmergenceResolution:
    return EmergenceResolution(
        resolved_year=resolved_year,
        source_field=source_field,
        fallback_used=source_field is not None and source_field != "first_known_year",
        is_modern_window=is_modern_window,
        window_start_year=2021,
        window_end_year=2026,
        note=note,
    )


def test_emergence_type_bridge_artist() -> None:
    e = _make_emergence(source_field="first_known_year", is_modern_window=True)
    assert compute_emergence_type(e, "bridge_artist") == "bridge_artist"


def test_emergence_type_formed_recent() -> None:
    e = _make_emergence(source_field="formed_year", is_modern_window=True)
    assert compute_emergence_type(e, "modern_echo") == "formed_recent"


def test_emergence_type_first_known_recent() -> None:
    e = _make_emergence(source_field="first_known_year", is_modern_window=True)
    assert compute_emergence_type(e, "modern_echo") == "first_known_recent"


def test_emergence_type_breakout_recent() -> None:
    e = _make_emergence(source_field="emergence_year", is_modern_window=True)
    assert compute_emergence_type(e, "modern_echo") == "breakout_recent"


def test_emergence_type_debut_recent() -> None:
    e = _make_emergence(source_field="debut_year", is_modern_window=True)
    assert compute_emergence_type(e, "modern_echo") == "debut_recent"


def test_emergence_type_established() -> None:
    e = _make_emergence(source_field="first_known_year", is_modern_window=False)
    assert compute_emergence_type(e, "modern_echo") == "established"


def test_emergence_type_unknown() -> None:
    e = _make_emergence(source_field=None, is_modern_window=False, resolved_year=None, note="unresolved_year")
    assert compute_emergence_type(e, "modern_echo") == "unknown"
