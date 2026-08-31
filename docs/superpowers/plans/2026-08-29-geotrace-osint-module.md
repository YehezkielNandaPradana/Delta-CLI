# GeoTrace OSINT Geolocation Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete GeoTrace OSINT Geolocation module for Delta AI Agent with multi-vector extraction, credibility scoring, cryptographic audit logging, safety guardrails, CLI/tool-calling schemas, tests, and web UI sidebar integration.

**Architecture:** Modular pipeline consisting of collector (data ingestion), extractor (multi-source geolocation features), scorer (evidence weighting and cross-validation clustering), report (dual-format reporting), audit (immutable SQLite hash chaining), vision adapter (hybrid LLM/heuristic vision), and Delta tool/web integration.

**Tech Stack:** Python 3.10+, SQLite3, Hashlib, Tailwind CSS glassmorphism, HTML5/Vanilla JS, pytest.

## Global Constraints
- Only access publicly available endpoints and metadata without private account scraping or login requirements.
- Obfuscate non-consensual coordinate resolution to city-level (~0.05 degree / ~5 km) under anti-doxxing policies.
- Refuse private accounts (`REJECTED_PRIVATE`) and accounts with minor indicators (`REJECTED_MINOR`).
- Provide cryptographic tamper-evident SHA-256 hash chains for the audit log.

---

### Task 1: Credibility Scorer & Cluster Analyzer (`delta/modules/geotrace/scorer.py`)

**Files:**
- Create: `delta/modules/geotrace/scorer.py`
- Test: `tests/test_geotrace_scorer.py`

**Interfaces:**
- Consumes: `LocationCandidate` from `delta.modules.geotrace.extractor`
- Produces: `ScoredLocation`, `GeoTraceResult`, `GeoTraceScorer` class

- [ ] **Step 1: Write failing test for Scorer**

```python
# tests/test_geotrace_scorer.py
import pytest
from delta.modules.geotrace.extractor import LocationCandidate
from delta.modules.geotrace.scorer import GeoTraceScorer, ScoredLocation, GeoTraceResult

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
    assert result.primary_location.city == "Jakarta"
    assert result.primary_location.confidence >= 70.0
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
    assert result.primary_location.city == "Bandung"
    # Multi-source corroboration must yield high confidence (> 90)
    assert result.primary_location.confidence >= 90.0
    assert len(result.primary_location.supporting_sources) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_geotrace_scorer.py -v`
Expected: FAIL (module `scorer` not found or classes missing).

- [ ] **Step 3: Implement `delta/modules/geotrace/scorer.py`**

```python
"""
GeoTrace Scorer & Cluster Engine.
Evaluates location candidates, calculates confidence scores (0-100),
applies cross-validation boosts, and clusters geographic evidence.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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

        for (norm_city, norm_country), group in cluster_groups.items():
            rep = group[0]
            unique_sources = set(c.source_type for c in group)
            reasons = []
            
            # Base score from maximum single candidate confidence
            max_base = max(c.confidence_base for c in group)
            
            # Calculate weighted average boost
            weighted_boost = 0.0
            for c in group:
                weight = self.WEIGHT_MAP.get(c.source_type, 0.1)
                weighted_boost += (c.confidence_base * 0.1) * weight
                reasons.append(f"[{c.source_type}] {c.evidence_snippet} (Base: {c.confidence_base:.0f}%)")

            # Cross-validation boost for multi-source confirmation
            multi_source_bonus = 0.0
            if len(unique_sources) >= 3:
                multi_source_bonus = 15.0
            elif len(unique_sources) >= 2:
                multi_source_bonus = 10.0

            final_confidence = min(99.5, max_base * 0.8 + weighted_boost + multi_source_bonus)

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_geotrace_scorer.py -v`
Expected: PASS

---

### Task 2: Hybrid Vision Adapter & Unit Tests for Extractor (`delta/modules/geotrace/vision_adapter.py` & `tests/test_geotrace_extractor.py`)

**Files:**
- Create: `delta/modules/geotrace/vision_adapter.py`
- Test: `tests/test_geotrace_extractor.py`

- [ ] **Step 1: Write unit tests for Extractor**

```python
# tests/test_geotrace_extractor.py
import pytest
from delta.modules.geotrace.collector import PublicDataCollector, PublicProfileData
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
    assert candidates[0].city == "Bandung"
    assert candidates[0].source_type == "EXIF_GPS"
    assert candidates[0].confidence_base == 95.0
```

- [ ] **Step 2: Run extractor test to verify it passes**

Run: `pytest tests/test_geotrace_extractor.py -v`
Expected: PASS

- [ ] **Step 3: Implement `delta/modules/geotrace/vision_adapter.py`**

```python
"""
Hybrid Vision Adapter for GeoTrace.
Analyzes public images for geolocation cues (landmarks, signage, vehicle plates, vegetation).
Utilizes Delta LLM Multimodal Vision if available, otherwise executes regex & heuristic rule matchers.
"""

import re
from typing import Any, Dict, List, Optional


class GeoTraceVisionAdapter:
    """
    Hybrid Vision processor for visual OSINT analysis.
    """

    KNOWN_LANDMARKS = [
        "monas", "bundaran hi", "gedung sate", "jalan braga", "candi prambanan",
        "candi borobudur", "malioboro", "jembatan suramadu", "gwk", "pantai kuta",
        "merlion", "petronas towers", "eiffel tower", "shibuya crossing"
    ]

    PLATE_PATTERNS = [
        r"\b([A-Z]{1,2})\s*\d{1,4}\s*[A-Z]{0,3}\b"
    ]

    def analyze_image_heuristics(self, image_metadata: Dict[str, Any], raw_text: str = "") -> List[str]:
        """
        Extract visual clues from image caption, OCR text, or mock detection labels.
        """
        clues = []
        combined_text = (raw_text + " " + " ".join(image_metadata.get("tags", []))).lower()

        for lm in self.KNOWN_LANDMARKS:
            if lm in combined_text:
                clues.append(f"Landmark {lm.title()} detected")

        for pattern in self.PLATE_PATTERNS:
            matches = re.findall(pattern, raw_text)
            for m in matches:
                clues.append(f"Vehicle plate prefix {m} observed")

        return clues

    def analyze_multimodal(self, image_url: str, prompt_hint: str = "") -> List[str]:
        """
        Analyzes image using vision pipeline. Fallback to heuristic parser.
        """
        # Heuristic fallback
        return self.analyze_image_heuristics({}, raw_text=prompt_hint)
```

---

### Task 3: Dual-Format Reporter & README Documentation (`delta/modules/geotrace/report.py` & `delta/modules/geotrace/README.md`)

**Files:**
- Create: `delta/modules/geotrace/report.py`
- Create: `delta/modules/geotrace/README.md`
- Test: `tests/test_geotrace_report.py`

- [ ] **Step 1: Write test for Report Generator**

```python
# tests/test_geotrace_report.py
import pytest
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
    assert json_out["primary_location"]["city"] == "Jakarta"
    assert json_out["primary_location"]["confidence"] == 88.5

    md_out = reporter.to_markdown(result)
    assert "# GeoTrace OSINT Geolocation Report" in md_out
    assert "Jakarta" in md_out
    assert "UU PDP" in md_out
```

- [ ] **Step 2: Implement `delta/modules/geotrace/report.py`**

```python
"""
GeoTrace Report Generator Module.
Generates structured JSON payloads and human-readable Markdown intelligence briefs.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict

from delta.modules.geotrace.scorer import GeoTraceResult


class GeoTraceReportGenerator:
    """
    Dual-format report generator with compliance notices and evidence matrices.
    """

    LEGAL_DISCLAIMER = (
        "> **LEGAL & ETHICAL NOTICE**:\n"
        "> This intelligence brief was generated strictly using publicly available OSINT data.\n"
        "> Processing conforms to Indonesia **UU PDP No. 27/2022** and **GDPR** legitimate interest principles.\n"
        "> Coordinate resolution is obfuscated to ~5 km unless explicit subject consent was recorded."
    )

    def to_json(self, result: GeoTraceResult) -> Dict[str, Any]:
        """Convert GeoTraceResult to clean, serializable JSON format."""
        primary_dict = asdict(result.primary_location) if result.primary_location else None
        clusters_dict = [asdict(c) for c in result.clusters]
        
        return {
            "target": result.target_handle,
            "status": result.status,
            "consent_mode": result.consent_mode,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "primary_location": primary_dict,
            "clusters": clusters_dict,
            "total_candidates_analyzed": len(result.raw_candidates),
            "notes": result.notes,
            "compliance": {
                "frameworks": ["UU_PDP_27_2022", "GDPR_ART_6_1_F"],
                "obfuscation_applied": result.primary_location.is_obfuscated if result.primary_location else False
            }
        }

    def to_markdown(self, result: GeoTraceResult) -> str:
        """Generate formatted executive markdown brief."""
        lines = [
            "# GeoTrace OSINT Geolocation Report",
            f"**Target Handle**: `{result.target_handle}` | **Status**: `{result.status}` | **Consent Mode**: `{'Active' if result.consent_mode else 'Standard (Obfuscated)'}`",
            f"**Timestamp**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            self.LEGAL_DISCLAIMER,
            "",
            "## 1. Executive Summary"
        ]

        if not result.primary_location:
            lines.append("No definitive geographic footprint could be established from public sources.")
            return "\n".join(lines)

        p = result.primary_location
        obf_text = "(Obfuscated to ~5 km city radius)" if p.is_obfuscated else "(Exact explicit/consent coordinates)"
        lines.extend([
            f"- **Estimated Location**: **{p.city}, {p.region_province}, {p.country} ({p.country_code})**",
            f"- **Confidence Level**: `{p.confidence:.1f}%`",
            f"- **Approx Coordinates**: `{p.latitude}, {p.longitude}` {obf_text}",
            f"- **Corroborating Evidence**: {p.evidence_count} signals across {len(p.supporting_sources)} distinct vectors ({', '.join(p.supporting_sources)})",
            "",
            "## 2. Evidence Matrix & Rationales"
        ])

        for r in p.detailed_reasons:
            lines.append(f"- {r}")

        if len(result.clusters) > 1:
            lines.extend([
                "",
                "## 3. Alternative Geographic Clusters",
                "| City / Region | Country | Confidence | Evidence Count |",
                "| :--- | :--- | :--- | :--- |"
            ])
            for alt in result.clusters[1:]:
                lines.append(f"| {alt.city}, {alt.region_province} | {alt.country} | {alt.confidence:.1f}% | {alt.evidence_count} |")

        return "\n".join(lines)
```

- [ ] **Step 3: Run report tests to verify it passes**

Run: `pytest tests/test_geotrace_report.py -v`
Expected: PASS

- [ ] **Step 4: Create `delta/modules/geotrace/README.md`**

Write legal, architectural, and ethical documentation.

---

### Task 4: Complete Package Engine & Delta Tool-Calling Integration (`delta/modules/geotrace/__init__.py` & `delta/ai/tools.py`)

**Files:**
- Create: `delta/modules/geotrace/__init__.py`
- Modify: `delta/ai/tools.py`
- Test: `tests/test_geotrace_tool.py`

- [ ] **Step 1: Write test for Tool Calling execution**

```python
# tests/test_geotrace_tool.py
import pytest
from delta.ai.tools import get_registry

def test_geotrace_tool_registration():
    registry = get_registry()
    tool = registry.get("geotrace_investigate")
    assert tool is not None
    assert tool.category == "osint"
    assert any(p.name == "target" for p in tool.parameters)
    assert any(p.name == "purpose" for p in tool.parameters)

def test_geotrace_tool_invocation():
    registry = get_registry()
    tool = registry.get("geotrace_investigate")
    result = tool.func(
        target="@johndoe_jakarta",
        operator="analyst-01",
        purpose="Legitimate KYC security check",
        consent_mode=False
    )
    assert "target" in result
    assert "primary_location" in result or "status" in result
```

- [ ] **Step 2: Implement `delta/modules/geotrace/__init__.py`**

```python
"""
GeoTrace OSINT Geolocation Package.
Unified interface for investigative geolocation intelligence.
"""

from delta.modules.geotrace.audit import GeoTraceAuditManager, SafetyGateException, AuditRecord
from delta.modules.geotrace.collector import PublicDataCollector, PublicProfileData, MediaMetadata, PublicPostData
from delta.modules.geotrace.extractor import GeoCandidateExtractor, LocationCandidate
from delta.modules.geotrace.scorer import GeoTraceScorer, ScoredLocation, GeoTraceResult
from delta.modules.geotrace.report import GeoTraceReportGenerator
from delta.modules.geotrace.vision_adapter import GeoTraceVisionAdapter


class GeoTraceEngine:
    """
    Main orchestrator for GeoTrace OSINT investigations.
    """

    def __init__(self, db_path: str = None):
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
        mock_profile: PublicProfileData = None
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
        profile = mock_profile or self.collector.build_mock_profile_for_testing(target)

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
```

- [ ] **Step 3: Register `geotrace_investigate` in `delta/ai/tools.py`**

Modify `delta/ai/tools.py` to register the `geotrace_investigate` tool in `_init_default_tools()`.

- [ ] **Step 4: Run tests to verify tool registration and invocation**

Run: `pytest tests/test_geotrace_tool.py -v`
Expected: PASS

---

### Task 5: Web API Endpoints & Server Handlers (`delta/web/server.py`)

**Files:**
- Modify: `delta/web/server.py`
- Test: `tests/test_geotrace_web.py`

- [ ] **Step 1: Write test for Web API endpoints**

```python
# tests/test_geotrace_web.py
import json
import pytest
from delta.modules.geotrace import GeoTraceEngine

def test_geotrace_audit_integrity():
    engine = GeoTraceEngine()
    engine.investigate("@test_user_jakarta", operator="web-admin", purpose="Testing integrity")
    valid, issues = engine.audit_mgr.verify_log_integrity()
    assert valid is True
    assert len(issues) == 0
```

- [ ] **Step 2: Add REST routes to `delta/web/server.py`**

- `POST /api/geotrace/analyze`: Accepts `{target, operator, purpose, consent_mode}`. Runs `GeoTraceEngine.investigate()`. Returns JSON report.
- `GET /api/geotrace/audit`: Returns recent audit logs from SQLite.
- `POST /api/geotrace/verify-audit`: Calls `verify_log_integrity()` and returns `{valid: bool, issues: []}`.

- [ ] **Step 3: Run web tests to verify endpoint handlers**

Run: `pytest tests/test_geotrace_web.py -v`
Expected: PASS

---

### Task 6: Web UI Sidebar Menu & Investigation Workspace (`delta/web/index.html` & `delta/web/static/index.html`)

**Files:**
- Modify: `delta/web/index.html`
- Modify: `delta/web/static/index.html`

- [ ] **Step 1: Add GeoTrace menu to Sidebar Navigation**

Insert sidebar button with icon `location_on` / `radar` and tooltip "GeoTrace OSINT".

- [ ] **Step 2: Add GeoTrace Investigation View Workspace**

Implement responsive glassmorphic panel containing:
- Input form: Target handle / URL, Operator ID, Purpose, Consent toggle.
- Primary Location Banner: Estimated City/Country, Confidence gauge bar, Obfuscation badge.
- Candidates Table & Multi-Vector Evidence Matrix.
- Audit Log Viewer with "Verify Hash Chain Integrity" button and verification indicator.
- Client-side JS handlers for calling `/api/geotrace/analyze`, `/api/geotrace/audit`, and `/api/geotrace/verify-audit`.

- [ ] **Step 3: Verify Web UI rendering and interactivity**

---

### Task 7: Comprehensive Verification & Audit Integrity Self-Check

- [ ] **Step 1: Run full GeoTrace test suite**
Run: `pytest tests/test_geotrace_*.py -v`
Expected: All tests PASS.

- [ ] **Step 2: Verify zero codebase regressions**
Run: `pytest tests/ -v`
Expected: All Delta tests PASS.
