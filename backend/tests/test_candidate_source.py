from backend.app.candidates import (
    CandidateSourceRecord,
    SourceName,
    all_source_statuses,
    merge_candidate_records,
    source_status,
)


class TestSourceName:
    def test_manual_pool_is_active(self) -> None:
        assert source_status(SourceName.MANUAL_POOL) == "active"

    def test_planned_sources_are_planned(self) -> None:
        for s in (SourceName.LASTFM_GRAPH, SourceName.MUSICBRAINZ, SourceName.SPOTIFY):
            assert source_status(s) == "planned"

    def test_all_source_statuses_includes_all(self) -> None:
        statuses = all_source_statuses()
        assert statuses["manual_pool"] == "active"
        assert statuses["lastfm_graph"] == "planned"
        assert statuses["musicbrainz"] == "planned"
        assert statuses["spotify"] == "planned"


class TestCandidateSourceRecord:
    def test_minimal_record(self) -> None:
        rec = CandidateSourceRecord(
            source_name="manual_pool",
            artist_name="Test Artist",
            related_seed="Manchester Orchestra",
        )
        assert rec.artist_name == "Test Artist"
        assert rec.source_name == "manual_pool"
        assert rec.confidence_signal == 0.0
        assert rec.tags == []
        assert rec.emergence_year is None

    def test_full_record(self) -> None:
        rec = CandidateSourceRecord(
            source_name=SourceName.MANUAL_POOL,
            artist_name="Home Is Where",
            related_seed="Manchester Orchestra",
            confidence_signal=0.85,
            tags=["emo", "indie rock", "post-hardcore"],
            emergence_year=2021,
            first_known_year=2021,
            formed_year=2020,
            emotional_tones=["urgent", "vulnerable"],
            lyrical_themes=["existential doubt", "relationships"],
            production_style="lo-fi emo with dynamic builds",
            vocal_style="passionate tenor",
            scene_lineage="Florida DIY emo scene",
            match_explanation="Recommended by curator for similarity to Manchester Orchestra",
            external_urls={"spotify": "https://open.spotify.com/artist/abc123"},
        )
        assert rec.source_name == "manual_pool"
        assert rec.emergence_year == 2021
        assert len(rec.tags) == 3
        assert rec.external_urls["spotify"].startswith("https://")

    def test_roundtrip_via_model_validate(self) -> None:
        data = {
            "source_name": "lastfm_graph",
            "artist_name": "Similar Band",
            "related_seed": "Thrice",
            "confidence_signal": 0.72,
            "tags": ["post-hardcore", "alternative rock"],
            "match_explanation": "Similar listener profiles on Last.fm",
        }
        rec = CandidateSourceRecord.model_validate(data)
        assert rec.source_name == "lastfm_graph"
        assert rec.confidence_signal == 0.72
        assert rec.emergence_year is None


class TestMergeCandidateRecords:
    def test_single_record_unchanged(self) -> None:
        rec = CandidateSourceRecord(
            source_name="manual_pool",
            artist_name="Test Artist",
            related_seed="Seed",
            confidence_signal=0.8,
        )
        merged = merge_candidate_records([rec])
        assert merged is not None
        assert merged.artist_name == "Test Artist"
        assert merged.source_name == "manual_pool"

    def test_empty_list_returns_none(self) -> None:
        assert merge_candidate_records([]) is None

    def test_merge_two_sources_for_same_artist(self) -> None:
        manual = CandidateSourceRecord(
            source_name="manual_pool",
            artist_name="Home Is Where",
            related_seed="Manchester Orchestra",
            confidence_signal=0.8,
            tags=["emo", "indie rock"],
            emergence_year=2021,
        )
        lastfm = CandidateSourceRecord(
            source_name="lastfm_graph",
            artist_name="Home Is Where",
            related_seed="Manchester Orchestra",
            confidence_signal=0.65,
            tags=["emo", "post-hardcore"],
            first_known_year=2020,
            match_explanation="Similar listener profiles",
        )
        merged = merge_candidate_records([manual, lastfm])
        assert merged is not None
        assert merged.source_name == "lastfm_graph/manual_pool"
        assert merged.confidence_signal == 0.8
        assert sorted(merged.tags) == ["emo", "indie rock", "post-hardcore"]
        assert merged.emergence_year == 2021
        assert merged.first_known_year == 2020

    def test_merge_picks_longer_text_field(self) -> None:
        brief = CandidateSourceRecord(
            source_name="manual_pool",
            artist_name="Artist",
            related_seed="Seed",
            production_style="indie rock",
        )
        detailed = CandidateSourceRecord(
            source_name="musicbrainz",
            artist_name="Artist",
            related_seed="Seed",
            production_style="indie rock with emo and post-hardcore influences",
        )
        merged = merge_candidate_records([brief, detailed])
        assert merged is not None
        assert merged.production_style == detailed.production_style

    def test_merge_concatenates_explanations(self) -> None:
        a = CandidateSourceRecord(
            source_name="manual_pool",
            artist_name="Artist",
            related_seed="Seed",
            match_explanation="Curator pick",
        )
        b = CandidateSourceRecord(
            source_name="spotify",
            artist_name="Artist",
            related_seed="Seed",
            match_explanation="Algorithmic recommendation",
        )
        merged = merge_candidate_records([a, b])
        assert merged is not None
        assert "Curator pick" in merged.match_explanation
        assert "Algorithmic recommendation" in merged.match_explanation

    def test_merge_three_sources(self) -> None:
        sources = [
            CandidateSourceRecord(
                source_name="manual_pool",
                artist_name="Same Artist",
                related_seed="Seed",
                tags=["emo"],
            ),
            CandidateSourceRecord(
                source_name="lastfm_graph",
                artist_name="Same Artist",
                related_seed="Seed",
                tags=["indie rock"],
            ),
            CandidateSourceRecord(
                source_name="musicbrainz",
                artist_name="Same Artist",
                related_seed="Seed",
                tags=["post-hardcore"],
            ),
        ]
        merged = merge_candidate_records(sources)
        assert merged is not None
        assert len(merged.source_name.split("/")) == 3
        assert set(merged.tags) == {"emo", "indie rock", "post-hardcore"}
