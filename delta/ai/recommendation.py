# delta/ai/recommendation.py

"""

Recommendation Engine - Provides automated security recommendations based on findings.

"""

from typing import Any, Dict, List, Optional

from delta.ai.reasoning import AnalysisResult, Finding

from delta.ai.knowledge import KnowledgeBase

class RecommendationEngine:

    """

    Generates prioritized security recommendations from analysis findings.

    Provides actionable remediation steps with references.

    """

    def __init__(self, knowledge_base: KnowledgeBase):

        self.knowledge = knowledge_base

    def generate_recommendations(self, analysis: AnalysisResult) -> List[Dict[str, Any]]:

        """Generate prioritized recommendations from analysis."""

        recommendations = []

        for finding in analysis.findings:

            rec = self._build_recommendation(finding)

            if rec:

                recommendations.append(rec)

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

        recommendations.sort(key=lambda r: severity_order.get(r["severity"], 99))

        return recommendations

    def summary(self, recommendations: List[Dict[str, Any]]) -> Dict[str, int]:

        """Get summary counts of recommendations by severity."""

        counts: Dict[str, int] = {}

        for rec in recommendations:

            sev = rec.get("severity", "info")

            counts[sev] = counts.get(sev, 0) + 1

        return counts

    def _build_recommendation(self, finding: Finding) -> Dict[str, Any]:

        """Build a structured recommendation from a finding."""

        return {

            "title": finding.title,

            "severity": finding.severity,

            "description": finding.description,

            "remediation": finding.recommendation,

            "references": finding.references,

            "priority": self._get_priority(finding.severity),

            "effort": self._get_effort(finding.severity),

        }

    def _get_priority(self, severity: str) -> str:

        """Get remediation priority based on severity."""

        priorities = {

            "critical": "IMMEDIATE - Remediate within 24 hours",

            "high": "HIGH - Remediate within 72 hours",

            "medium": "MEDIUM - Remediate within 1 week",

            "low": "LOW - Remediate within 1 month",

            "info": "INFORMATIONAL - Review and document",

        }

        return priorities.get(severity.lower(), "INFORMATIONAL")

    def _get_effort(self, severity: str) -> str:

        """Get estimated remediation effort."""

        efforts = {

            "critical": "High - May require immediate patching or mitigation",

            "high": "Medium-High - May require configuration changes",

            "medium": "Medium - Configuration or code change required",

            "low": "Low - Simple configuration change",

            "info": "None - Informational only",

        }

        return efforts.get(severity.lower(), "Unknown")