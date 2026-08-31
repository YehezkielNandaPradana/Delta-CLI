from delta.modules.geotrace.extractor import LocationCandidate
from delta.modules.geotrace.scorer import GeoTraceScorer, GeoTraceResult

def test_scorer_single_candidate():
    scorer = GeoTraceScorer()
    candidates = [
        LocationCandidate(
            source_type="TEXTUAL_BIO",
            city="Jakarta",
            region_province="DKI Jakarta",
            country="Indonesia",
            country_code="ID",
            latitude_approx=-6.2088,
            longitude_approx=106.8456,
            confidence_base=70.0,
            evidence_snippet="Bio mentions Jakarta",
            raw_signal="Jakarta"
        )
    ]
    result = scorer.score_candidates(candidates, target_handle="test_user", consent_mode=False)
    assert isinstance(result, GeoTraceResult)
    assert len(result.clusters) == 1
    assert result.primary_location is not None
    assert result.primary_location.city == "Jakarta"
    assert result.primary_location.confidence >= 50.0
    assert result.primary_location.is_obfuscated is True

def test_scorer_cross_validation_boost():
    scorer = GeoTraceScorer()
    candidates = [
        LocationCandidate(
            source_type="TEXTUAL_BIO",
            city="Bandung",
            region_province="Jawa Barat",
            country="Indonesia",
            country_code="ID",
            latitude_approx=-6.9175,
            longitude_approx=107.6191,
            confidence_base=70.0,
            evidence_snippet="Bio mentions Bandung"
        ),
        LocationCandidate(
            source_type="VISUAL_AI",
            city="Bandung",
            region_province="Jawa Barat",
            country="Indonesia",
            country_code="ID",
            latitude_approx=-6.9175,
            longitude_approx=107.6191,
            confidence_base=75.0,
            evidence_snippet="Vehicle plate D detected"
        ),
        LocationCandidate(
            source_type="EXPLICIT_GEOTAG",
            city="Bandung",
            region_province="Jawa Barat",
            country="Indonesia",
            country_code="ID",
            latitude_approx=-6.9175,
            longitude_approx=107.6191,
            confidence_base=90.0,
            evidence_snippet="Geotagged Bandung"
        )
    ]
    result = scorer.score_candidates(candidates, target_handle="bandung_user", consent_mode=True)
    assert result.primary_location is not None
    assert result.primary_location.city == "Bandung"
    assert result.primary_location.confidence >= 90.0
    assert len(result.primary_location.supporting_sources) >= 3
