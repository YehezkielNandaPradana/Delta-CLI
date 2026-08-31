from delta.modules.geotrace.scorer import GeoTraceResult, ScoredLocation
from delta.modules.geotrace.report import GeoTraceReportGenerator

def test_report_generation():
    primary = ScoredLocation(
        city="Jakarta",
        region_province="DKI Jakarta",
        country="Indonesia",
        country_code="ID",
        latitude=-6.2088,
        longitude=106.8456,
        confidence=88.5,
        is_obfuscated=True,
        evidence_count=2,
        supporting_sources=["TEXTUAL_BIO", "VISUAL_AI"],
        detailed_reasons=["[TEXTUAL_BIO] Bio mentions Jakarta", "[VISUAL_AI] Monas spotted"]
    )
    result = GeoTraceResult(
        target_handle="@target_investigation",
        consent_mode=False,
        primary_location=primary,
        clusters=[primary]
    )
    reporter = GeoTraceReportGenerator()
    json_out = reporter.to_json(result)
    assert json_out["target"] == "@target_investigation"
    assert json_out["primary_location"] is not None
    assert json_out["primary_location"]["city"] == "Jakarta"
    assert json_out["primary_location"]["confidence"] == 88.5

    md_out = reporter.to_markdown(result)
    assert "# GeoTrace OSINT Geolocation Report" in md_out
    assert "Jakarta" in md_out
    assert "UU PDP" in md_out
