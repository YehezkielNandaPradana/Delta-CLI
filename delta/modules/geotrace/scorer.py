"""
GeoTrace Scorer & Cluster Engine.
Evaluates location candidates, calculates confidence scores (0-100),
applies cross-validation boosts, and clusters geographic evidence.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from delta.modules.geotrace.extractor import LocationCandidate


@dataclass
class ScoredLocation:
    city: str
    region_province: str
    country: str
    country_code: str
    latitude: Optional[float]
    longitude: Optional[float]
    confidence: float
    is_obfuscated: bool
    evidence_count: int
    supporting_sources: List[str] = field(default_factory=list)
    detailed_reasons: List[str] = field(default_factory=list)


@dataclass
class GeoTraceResult:
    target_handle: str
    consent_mode: bool
    primary_location: Optional[ScoredLocation]
    clusters: List[ScoredLocation] = field(default_factory=list)
    raw_candidates: List[LocationCandidate] = field(default_factory=list)
    status: str = "SUCCESS"
    notes: str = ""


class GeoTraceScorer:
    """
    Evidence-Weighted Credibility Engine.
    Combines weighted signals from EXIF, geotags, visual cues, bio text, and temporal patterns.
    """

    WEIGHT_MAP = {
        "EXIF_GPS": 0.35,
        "EXPLICIT_GEOTAG": 0.25,
        "VISUAL_AI": 0.20,
        "TEXTUAL_BIO": 0.12,
        "TEMPORAL_TIMEZONE": 0.08,
    }

    def score_candidates(
        self,
        candidates: List[LocationCandidate],
        target_handle: str,
        consent_mode: bool = False
    ) -> GeoTraceResult:
        if not candidates:
            return GeoTraceResult(
                target_handle=target_handle,
                consent_mode=consent_mode,
                primary_location=None,
                clusters=[],
                raw_candidates=[],
                status="NO_SIGNALS_FOUND",
                notes="No geographic clues found in public footprint."
            )

        # Group by normalized (city, country)
        cluster_groups: Dict[Tuple[str, str], List[LocationCandidate]] = defaultdict(list)
        for c in candidates:
            key = (c.city.strip().lower(), c.country.strip().lower())
            cluster_groups[key].append(c)

        scored_clusters: List[ScoredLocation] = []

        for group in cluster_groups.values():
            rep = group[0]
            unique_sources = set(c.source_type for c in group)
            reasons = []

            # Base score from maximum single candidate confidence
            max_base = max(c.confidence_base for c in group)

            # Calculate weighted corroboration score
            weighted_boost = sum(c.confidence_base * self.WEIGHT_MAP.get(c.source_type, 0.1) for c in group)
            for c in group:
                reasons.append(f"[{c.source_type}] {c.evidence_snippet} (Base: {c.confidence_base:.0f}%)")

            # Cross-validation boost for multi-source confirmation
            multi_source_bonus = 0.0
            if len(unique_sources) >= 4:
                multi_source_bonus = 20.0
            elif len(unique_sources) == 3:
                multi_source_bonus = 15.0
            elif len(unique_sources) == 2:
                multi_source_bonus = 10.0

            # High precision confidence aggregator
            final_confidence = min(99.5, max_base * 0.8 + weighted_boost * 0.15 + multi_source_bonus)

            # Determine coordinates and obfuscation
            use_lat = rep.latitude_approx
            use_lon = rep.longitude_approx
            is_obf = False

            if not consent_mode and not rep.is_precise_explicit:
                is_obf = True
                if use_lat is not None and use_lon is not None:
                    # Quantize to ~5km
                    use_lat = round(round(use_lat / 0.05) * 0.05, 4)
                    use_lon = round(round(use_lon / 0.05) * 0.05, 4)

            scored_clusters.append(ScoredLocation(
                city=rep.city,
                region_province=rep.region_province,
                country=rep.country,
                country_code=rep.country_code,
                latitude=use_lat,
                longitude=use_lon,
                confidence=round(final_confidence, 1),
                is_obfuscated=is_obf,
                evidence_count=len(group),
                supporting_sources=list(unique_sources),
                detailed_reasons=reasons
            ))

        # Sort clusters by confidence descending
        scored_clusters.sort(key=lambda x: x.confidence, reverse=True)
        primary = scored_clusters[0] if scored_clusters else None

        return GeoTraceResult(
            target_handle=target_handle,
            consent_mode=consent_mode,
            primary_location=primary,
            clusters=scored_clusters,
            raw_candidates=candidates,
            status="SUCCESS"
        )
