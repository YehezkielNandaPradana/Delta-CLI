"""
GeoTrace Report Generator Module.
Generates structured JSON payloads and human-readable Markdown intelligence briefs.
"""

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
