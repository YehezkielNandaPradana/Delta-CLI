"""
GeoTrace OSINT Geolocation Package.
Unified interface for investigative geolocation intelligence.
"""

from typing import Optional

from delta.modules.geotrace.audit import GeoTraceAuditManager, SafetyGateException, AuditRecord
from delta.modules.geotrace.collector import PublicDataCollector, PublicProfileData, MediaMetadata, PublicPostData
from delta.modules.geotrace.extractor import GeoCandidateExtractor, LocationCandidate
from delta.modules.geotrace.geocoder import DynamicGeocoder
from delta.modules.geotrace.scorer import GeoTraceScorer, ScoredLocation, GeoTraceResult
from delta.modules.geotrace.report import GeoTraceReportGenerator
from delta.modules.geotrace.vision_adapter import GeoTraceVisionAdapter


class GeoTraceEngine:
    """
    Main orchestrator for GeoTrace OSINT investigations.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.audit_mgr = GeoTraceAuditManager(db_path=db_path)
        self.collector = PublicDataCollector()
        self.extractor = GeoCandidateExtractor()
        self.scorer = GeoTraceScorer()
        self.reporter = GeoTraceReportGenerator()
        self.vision = GeoTraceVisionAdapter()

    def investigate(
        self,
        target: str,
        operator: str = "delta-analyst",
        purpose: str = "OSINT Security Investigation",
        consent_mode: bool = False,
        mock_profile: Optional[PublicProfileData] = None
    ) -> GeoTraceResult:
        """
        Execute full investigation pipeline with safety gating and audit logging.
        """
        # 1. Rate limit check
        is_ok, rate_msg = self.audit_mgr.check_rate_limit(target)
        if not is_ok:
            self.audit_mgr.log_query(operator, target, purpose, consent_mode, "RATE_LIMITED", rate_msg)
            raise SafetyGateException(rate_msg)

        # 2. Acquire profile data (mock or normalized public footprint)
        profile = mock_profile or self.collector.collect_public_profile(target)

        # 3. Safety gate check (Minor & Private account refusal)
        is_safe, status_code, reason = self.audit_mgr.evaluate_target_safety({
            "is_private": profile.is_private,
            "bio": profile.bio,
            "username": profile.handle
        })

        if not is_safe:
            self.audit_mgr.log_query(operator, target, purpose, consent_mode, status_code, reason)
            raise SafetyGateException(reason)

        # 4. Extract candidates across all 5 vectors
        candidates = self.extractor.extract_all(profile)

        # 5. Score & Cluster
        result = self.scorer.score_candidates(candidates, target_handle=profile.handle, consent_mode=consent_mode)

        # 6. Append completed audit log
        self.audit_mgr.log_query(operator, target, purpose, consent_mode, "COMPLETED", "Analysis finished successfully")

        return result


__all__ = [
    "GeoTraceEngine",
    "GeoTraceAuditManager",
    "SafetyGateException",
    "AuditRecord",
    "PublicDataCollector",
    "PublicProfileData",
    "MediaMetadata",
    "PublicPostData",
    "GeoCandidateExtractor",
    "LocationCandidate",
    "GeoTraceScorer",
    "ScoredLocation",
    "GeoTraceResult",
    "GeoTraceReportGenerator",
    "GeoTraceVisionAdapter",
]
