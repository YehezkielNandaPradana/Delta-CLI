from delta.modules.geotrace.collector import PublicDataCollector
from delta.modules.geotrace.extractor import GeoCandidateExtractor

def test_extractor_bio_and_text():
    collector = PublicDataCollector()
    profile = collector.build_mock_profile_for_testing(
        handle="@johndoe",
        bio="Coffee lover in Surabaya and Malang. Exploring East Java."
    )
    extractor = GeoCandidateExtractor()
    candidates = extractor.extract_from_bio_and_text(profile)
    assert any(c.city == "Surabaya" for c in candidates)
    surabaya_c = next(c for c in candidates if c.city == "Surabaya")
    assert surabaya_c.country == "Indonesia"
    assert surabaya_c.source_type == "TEXTUAL_BIO"

def test_extractor_visual_clues():
    collector = PublicDataCollector()
    profile = collector.build_mock_profile_for_testing(
        handle="@photographer",
        posts=[{
            "post_id": "p1",
            "media": [{
                "url": "https://example.com/photo1.jpg",
                "visual_clues": ["Landmark Monas in background", "Vehicle plate B 1234 CD"]
            }]
        }]
    )
    extractor = GeoCandidateExtractor()
    candidates = extractor.extract_from_visual_clues(profile.posts)
    assert len(candidates) >= 2
    assert any(c.city == "Jakarta" and "Monas" in c.evidence_snippet for c in candidates)
    assert any(c.city == "Jakarta" and "plate prefix 'B'" in c.evidence_snippet for c in candidates)

def test_extractor_exif_metadata():
    collector = PublicDataCollector()
    profile = collector.build_mock_profile_for_testing(
        handle="@traveller",
        posts=[{
            "post_id": "p2",
            "media": [{
                "url": "https://example.com/exif.jpg",
                "exif": {
                    "lat": -6.9175,
                    "lon": 107.6191,
                    "make": "Canon",
                    "model": "EOS R5"
                }
            }]
        }]
    )
    extractor = GeoCandidateExtractor()
    candidates = extractor.extract_from_exif_metadata(profile.posts)
    assert len(candidates) == 1
    assert candidates[0].city in ("Bandung", "Kota Bandung")
    assert candidates[0].source_type == "EXIF_GPS"
    assert candidates[0].confidence_base == 95.0
