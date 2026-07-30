# delta/modules/analysis.py
"""
Analysis Module - Scan result analysis and vulnerability interpretation.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from delta.ai.knowledge import KnowledgeBase, VulnerabilityInfo
from delta.ai.reasoning import ReasoningEngine, AnalysisResult, Finding


class AnalysisModule:
    """
    Security analysis module that interprets scan results and provides explanations.
    Integrates with KnowledgeBase and ReasoningEngine for intelligent analysis.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge = knowledge_base
        self.reasoning = ReasoningEngine(knowledge_base)

    def analyze(self, target: str, scan_data: Dict[str, Any]) -> AnalysisResult:
        """Analyze scan data and generate findings with risk scoring."""
        if not scan_data:
            return AnalysisResult(target=target, risk_score=0.0)
        return self.reasoning.analyze_scan(target, scan_data)

    def explain_vulnerability(self, vuln_name: str) -> Optional[Dict[str, Any]]:
        """Explain a vulnerability with details."""
        vuln = self.knowledge.get_vulnerability(vuln_name)
        if vuln:
            return {
                "id": vuln.id,
                "name": vuln.name,
                "category": vuln.category,
                "severity": vuln.severity,
                "description": vuln.description,
                "impact": vuln.impact,
                "cause": vuln.possible_cause,
                "recommendation": vuln.recommendation,
                "references": vuln.references,
                "cwe": vuln.cwe,
                "owasp": vuln.owasp_category,
            }
        return None

    def explain_concept(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Explain a security concept."""
        concept = self.knowledge.get_concept(concept_name)
        if concept:
            return {
                "name": concept.name,
                "description": concept.description,
                "category": concept.category,
                "best_practice": concept.best_practice,
                "references": concept.references,
            }
        return None

    def search_vulnerabilities(self, query: str) -> List[Dict[str, Any]]:
        """Search for vulnerabilities matching query."""
        results = self.knowledge.search_vulnerabilities(query)
        return [
            {
                "id": v.id,
                "name": v.name,
                "severity": v.severity,
                "description": v.description[:100] + "...",
            }
            for v in results
        ]