from backend.app.candidates import SourceName
from backend.app.manual_pool import (
    DEFAULT_MANUAL_CONFIDENCE,
    ManualPoolSource,
    entry_to_candidate,
    is_eligible,
)


class TestIsEligible:
    def test_eligible_normal_entry(self) -> None:
        entry = {
            "name": "Home Is Where",
            "active_status": True,
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "tags": ["emo"],
        }
        assert is_eligible(entry, "Manchester Orchestra") is True

    def test_excluded_when_active_status_false(self) -> None:
        entry = {
            "name": "Inactive Artist",
            "active_status": False,
            "recommended_legacy_matches": ["Manchester Orchestra"],
        }
        assert is_eligible(entry, "Manchester Orchestra") is False

    def test_excluded_when_no_match(self) -> None:
        entry = {
            "name": "Unrelated Artist",
            "active_status": True,
            "recommended_legacy_matches": ["Thrice"],
        }
        assert is_eligible(entry, "Manchester Orchestra") is False

    def test_case_insensitive_seed_matching(self) -> None:
        entry = {
            "name": "Test Artist",
            "active_status": True,
            "recommended_legacy_matches": ["  manchester orchestra  "],
        }
        assert is_eligible(entry, "Manchester Orchestra") is True

    def test_fallback_to_related_legacy_styles(self) -> None:
        entry = {
            "name": "Test Artist",
            "active_status": True,
            "related_legacy_styles": ["Manchester Orchestra"],
        }
        assert is_eligible(entry, "Manchester Orchestra") is True

    def test_excluded_when_name_empty(self) -> None:
        entry = {
            "name": "",
            "active_status": True,
            "recommended_legacy_matches": ["Manchester Orchestra"],
        }
        assert is_eligible(entry, "Manchester Orchestra") is False

    def test_excluded_when_name_missing(self) -> None:
        entry = {
            "active_status": True,
            "recommended_legacy_matches": ["Manchester Orchestra"],
        }
        assert is_eligible(entry, "Manchester Orchestra") is False


class TestEntryToCandidate:
    def test_converts_basic_fields(self) -> None:
        entry = {
            "name": "Home Is Where",
            "tags": ["emo", "indie rock"],
            "formed_year": 2021,
            "first_known_year": 2021,
            "emotional_tones": ["urgent", "vulnerable"],
            "lyrical_themes": ["existential doubt"],
            "production_style": "lo-fi emo",
            "vocal_style": "passionate tenor",
            "scene_lineage": "Florida DIY emo scene",
            "source_note": "Emerging artist",
            "spotify_url": "https://open.spotify.com/artist/abc",
        }
        rec = entry_to_candidate(entry, "Manchester Orchestra")
        assert rec.artist_name == "Home Is Where"
        assert rec.source_name == SourceName.MANUAL_POOL.value
        assert rec.related_seed == "Manchester Orchestra"
        assert rec.confidence_signal == DEFAULT_MANUAL_CONFIDENCE
        assert rec.tags == ["emo", "indie rock"]
        assert rec.formed_year == 2021
        assert rec.first_known_year == 2021
        assert rec.emotional_tones == ["urgent", "vulnerable"]
        assert rec.match_explanation == "Emerging artist"
        assert rec.external_urls["spotify"] == "https://open.spotify.com/artist/abc"

    def test_handles_minimal_entry(self) -> None:
        entry = {"name": "Minimal Artist"}
        rec = entry_to_candidate(entry, "Seed")
        assert rec.artist_name == "Minimal Artist"
        assert rec.tags == []
        assert rec.emergence_year is None
        assert rec.emotional_tones == []
        assert rec.match_explanation == ""  # source_note missing
        assert rec.external_urls == {}

    def test_omits_empty_spotify_url(self) -> None:
        entry = {"name": "Artist", "spotify_url": ""}
        rec = entry_to_candidate(entry, "Seed")
        assert rec.external_urls == {}


class TestManualPoolSource:
    POOL = [
        {
            "name": "Home Is Where",
            "active_status": True,
            "recommended_legacy_matches": ["Manchester Orchestra", "Bright Eyes"],
            "tags": ["emo", "indie rock"],
            "formed_year": 2021,
            "first_known_year": 2021,
            "emotional_tones": ["urgent", "vulnerable"],
            "lyrical_themes": ["existential doubt"],
            "production_style": "lo-fi emo",
            "vocal_style": "passionate tenor",
            "scene_lineage": "Florida DIY emo scene",
            "source_note": "Emerging artist",
        },
        {
            "name": "Ben Quad",
            "active_status": True,
            "recommended_legacy_matches": ["Manchester Orchestra", "Thrice"],
            "tags": ["emo", "math rock"],
            "formed_year": 2020,
            "first_known_year": 2022,
            "emotional_tones": ["cathartic", "intense"],
            "lyrical_themes": ["relationships"],
            "production_style": "technical emo",
            "vocal_style": "melodic tenor",
            "scene_lineage": "Oklahoma DIY emo scene",
            "source_note": "Technical emo",
        },
        {
            "name": "Militarie Gun",
            "active_status": True,
            "recommended_legacy_matches": ["Thrice", "Thursday"],
            "tags": ["post-hardcore"],
            "source_note": "Melodic post-hardcore",
        },
        {
            "name": "Inactive Artist",
            "active_status": False,
            "recommended_legacy_matches": ["Manchester Orchestra"],
            "source_note": "Should be excluded",
        },
    ]

    def test_returns_eligible_candidates_for_seed(self) -> None:
        source = ManualPoolSource(self.POOL)
        candidates = source.get_candidates("Manchester Orchestra")
        names = {c.artist_name for c in candidates}
        assert "Home Is Where" in names
        assert "Ben Quad" in names
        assert "Militarie Gun" not in names
        assert "Inactive Artist" not in names

    def test_candidate_has_correct_source_name(self) -> None:
        source = ManualPoolSource(self.POOL)
        candidates = source.get_candidates("Manchester Orchestra")
        for c in candidates:
            assert c.source_name == SourceName.MANUAL_POOL.value

    def test_candidate_has_stable_confidence(self) -> None:
        source = ManualPoolSource(self.POOL)
        candidates = source.get_candidates("Manchester Orchestra")
        for c in candidates:
            assert c.confidence_signal == DEFAULT_MANUAL_CONFIDENCE

    def test_case_insensitive_seed_search(self) -> None:
        source = ManualPoolSource(self.POOL)
        upper = source.get_candidates("MANCHESTER ORCHESTRA")
        lower = source.get_candidates("manchester orchestra")
        padded = source.get_candidates("  Manchester Orchestra  ")
        assert len(upper) == len(lower) == len(padded) > 0

    def test_explainability_preserved(self) -> None:
        source = ManualPoolSource(self.POOL)
        candidates = source.get_candidates("Manchester Orchestra")
        by_name = {c.artist_name: c for c in candidates}
        home = by_name["Home Is Where"]
        assert home.match_explanation == "Emerging artist"
        assert home.related_seed == "Manchester Orchestra"
        assert home.source_name == SourceName.MANUAL_POOL.value

    def test_dedup_duplicate_entries_for_same_artist(self) -> None:
        pool = self.POOL + [
            {
                "name": "Home Is Where",
                "active_status": True,
                "recommended_legacy_matches": ["Manchester Orchestra"],
                "tags": ["folk punk"],
                "source_note": "Dup entry",
            }
        ]
        source = ManualPoolSource(pool)
        candidates = source.get_candidates("Manchester Orchestra")
        names = [c.artist_name for c in candidates]
        assert names.count("Home Is Where") == 1
        merged = [c for c in candidates if c.artist_name == "Home Is Where"][0]
        assert "emo" in merged.tags
        assert "folk punk" in merged.tags

    def test_different_seed_returns_different_candidates(self) -> None:
        source = ManualPoolSource(self.POOL)
        manchester = source.get_candidates("Manchester Orchestra")
        thrice = source.get_candidates("Thrice")
        manchester_names = {c.artist_name for c in manchester}
        thrice_names = {c.artist_name for c in thrice}
        assert "Home Is Where" in manchester_names
        assert "Home Is Where" not in thrice_names
        assert "Militarie Gun" not in manchester_names
        assert "Militarie Gun" in thrice_names
        assert "Inactive Artist" not in manchester_names
        assert "Inactive Artist" not in thrice_names

    def test_loads_pool_from_default_file(self) -> None:
        source = ManualPoolSource()
        candidates = source.get_candidates("Manchester Orchestra")
        assert len(candidates) > 0

    def test_no_candidates_for_unknown_seed(self) -> None:
        source = ManualPoolSource(self.POOL)
        candidates = source.get_candidates("Unknown Artist")
        assert candidates == []
