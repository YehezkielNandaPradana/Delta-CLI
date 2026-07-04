# delta/ai/reasoning.py
"""
Reasoning Pipeline - Simple inference engine for analyzing scan results and drawing conclusions.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from delta.ai.knowledge import KnowledgeBase, VulnerabilityInfo


@dataclass
class Finding:
    """A single security finding from analysis."""
    title: str
    severity: str  # critical, high, medium, low, info
    description: str
    evidence: str
    recommendation: str
    references: List[str] = field(default_factory=list)
    cwe: str = ""
    cvss_score: float = 0.0


@dataclass
class AnalysisResult:
    """Complete analysis result with findings and summary."""
    target: str
    summary: str
    risk_level: str
    findings: List[Finding] = field(default_factory=list)
    score: float = 0.0
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


class ReasoningEngine:
    """
    Analyzes scan results and generates security findings.
    Uses rules and knowledge base to interpret raw scan data.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge = knowledge_base
        self._analysis_rules = self._build_rules()

    def _build_rules(self) -> Dict[str, List[Dict]]:
        """Build analysis rules."""
        return {
            "open_ports": [
                {
                    "port_range": (1, 1024),
                    "finding": "System/Privileged Ports Open",
                    "severity": "medium",
                    "description": "Privileged ports (1-1024) are open and accessible.",
                },
                {
                    "port_range": (1025, 49151),
                    "finding": "Registered Ports Open",
                    "severity": "low",
                    "description": "Non-standard ports are open on the target.",
                },
            ],
            "web": [
                {
                    "header": "X-Frame-Options",
                    "missing": True,
                    "finding": "Missing Clickjacking Protection",
                    "severity": "medium",
                },
                {
                    "header": "X-Content-Type-Options",
                    "missing": True,
                    "finding": "Missing MIME-Sniffing Protection",
                    "severity": "low",
                },
                {
                    "header": "Strict-Transport-Security",
                    "missing": True,
                    "finding": "Missing HSTS Header",
                    "severity": "medium",
                },
                {
                    "header": "Content-Security-Policy",
                    "missing": True,
                    "finding": "Missing Content Security Policy",
                    "severity": "medium",
                },
                {
                    "header": "Server",
                    "pattern": r"(Apache|nginx|IIS|Tomcat)/?(\d+\.\d+)",
                    "finding": "Server Version Disclosure",
                    "severity": "low",
                },
            ],
        }

    def analyze_scan(self, target: str, scan_data: Dict[str, Any]) -> AnalysisResult:
        """Analyze complete scan data and generate findings."""
        findings = []
        
        # Analyze open ports
        if "open_ports" in scan_data:
            findings.extend(self._analyze_ports(scan_data["open_ports"]))
        
        # Analyze web headers
        if "headers" in scan_data:
            findings.extend(self._analyze_headers(scan_data["headers"]))
        
        # Analyze services
        if "services" in scan_data:
            findings.extend(self._analyze_services(scan_data["services"]))
        
        # Analyze SSL/TLS
        if "ssl" in scan_data:
            findings.extend(self._analyze_ssl(scan_data["ssl"]))

        # Calculate risk
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.severity.lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        risk_level = self._calculate_risk_level(severity_counts)
        total = sum(severity_counts.values())
        score = self._calculate_score(severity_counts)

        summary = self._generate_summary(target, severity_counts, risk_level)

        return AnalysisResult(
            target=target,
            summary=summary,
            risk_level=risk_level,
            findings=findings,
            score=score,
            total_findings=total,
            critical_count=severity_counts["critical"],
            high_count=severity_counts["high"],
            medium_count=severity_counts["medium"],
            low_count=severity_counts["low"],
        )

    def _analyze_ports(self, ports: List[Dict]) -> List[Finding]:
        """Analyze open ports for vulnerabilities."""
        findings = []
        dangerous_ports = {
            21: ("FTP", "FTP service may allow anonymous access or plaintext authentication."),
            23: ("Telnet", "Telnet transmits credentials in plaintext."),
            25: ("SMTP", "SMTP may be used for email spoofing or relay."),
            53: ("DNS", "DNS service may be vulnerable to amplification attacks."),
            445: ("SMB", "SMB may be vulnerable to remote code execution (EternalBlue)."),
            1433: ("MSSQL", "MSSQL exposed to network may allow brute force attacks."),
            3306: ("MySQL", "MySQL exposed to network may allow brute force attacks."),
            3389: ("RDP", "RDP exposed to network may allow brute force or BlueKeep attacks."),
            5432: ("PostgreSQL", "PostgreSQL exposed to network may allow brute force attacks."),
            27017: ("MongoDB", "MongoDB exposed without authentication may leak data."),
            6379: ("Redis", "Redis exposed without authentication may allow RCE."),
            9200: ("Elasticsearch", "Elasticsearch exposed may allow data access."),
        }

        for port_info in ports:
            port = port_info.get("port", 0)
            service = port_info.get("service", "unknown")
            
            if port in dangerous_ports:
                svc_name, desc = dangerous_ports[port]
                findings.append(Finding(
                    title=f"Dangerous Service Exposed: {svc_name} (Port {port})",
                    severity="high",
                    description=desc,
                    evidence=f"Port {port}/{service} is open and accessible",
                    recommendation=f"Restrict access to port {port} using firewall rules. If {svc_name} is not required, disable the service.",
                    cwe="CWE-200",
                ))

        return findings

    def _analyze_headers(self, headers: Dict[str, str]) -> List[Finding]:
        """Analyze HTTP security headers."""
        findings = []
        
        # Check for security headers
        security_headers = {
            "strict-transport-security": {
                "name": "Strict-Transport-Security (HSTS)",
                "severity": "medium",
                "desc": "Missing HSTS header allows downgrade attacks",
                "rec": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' header",
            },
            "x-frame-options": {
                "name": "X-Frame-Options",
                "severity": "medium",
                "desc": "Missing clickjacking protection",
                "rec": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN' header",
            },
            "x-content-type-options": {
                "name": "X-Content-Type-Options",
                "severity": "low",
                "desc": "Missing MIME-sniffing protection",
                "rec": "Add 'X-Content-Type-Options: nosniff' header",
            },
            "content-security-policy": {
                "name": "Content-Security-Policy",
                "severity": "medium",
                "desc": "Missing Content Security Policy increases XSS risk",
                "rec": "Implement a Content-Security-Policy header",
            },
            "x-xss-protection": {
                "name": "X-XSS-Protection",
                "severity": "low",
                "desc": "Missing XSS protection header",
                "rec": "Add 'X-XSS-Protection: 1; mode=block' header (deprecated but still useful)",
            },
            "referrer-policy": {
                "name": "Referrer-Policy",
                "severity": "low",
                "desc": "Missing Referrer-Policy may leak URL information",
                "rec": "Add 'Referrer-Policy: strict-origin-when-cross-origin' header",
            },
            "permissions-policy": {
                "name": "Permissions-Policy",
                "severity": "low",
                "desc": "Missing Permissions-Policy allows all API access",
                "rec": "Implement a Permissions-Policy header to restrict browser features",
            },
        }

        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        for header_key, info in security_headers.items():
            if header_key not in headers_lower:
                findings.append(Finding(
                    title=f"Missing Security Header: {info['name']}",
                    severity=info["severity"],
                    description=info["desc"],
                    evidence=f"The '{info['name']}' response header was not found",
                    recommendation=info["rec"],
                ))

        # Check server version disclosure
        if "server" in headers_lower:
            server = headers_lower["server"]
            findings.append(Finding(
                title="Server Version Disclosure",
                severity="low",
                description=f"The server header reveals: {server}. This information helps attackers identify vulnerable versions.",
                evidence=f"Server header: {server}",
                recommendation="Configure the web server to hide version information in server headers.",
                cwe="CWE-200",
            ))

        return findings

    def _analyze_services(self, services: Dict) -> List[Finding]:
        """Analyze detected services for known vulnerabilities."""
        findings = []
        # Service-specific analysis
        for service_name, service_info in services.items():
            version = service_info.get("version", "")
            if "http" in service_name.lower():
                findings.append(Finding(
                    title=f"Web Service Detected: {service_name}",
                    severity="info",
                    description=f"Web service {service_name} {version} detected. Requires further analysis for known CVEs.",
                    evidence=f"Service: {service_name} {version}",
                    recommendation="Check for known vulnerabilities in this version. Ensure it is patched and properly configured.",
                ))
        return findings

    def _analyze_ssl(self, ssl_data: Dict) -> List[Finding]:
        """Analyze SSL/TLS configuration."""
        findings = []
        
        if ssl_data.get("expired", False):
            findings.append(Finding(
                title="Expired SSL/TLS Certificate",
                severity="high",
                description="The SSL/TLS certificate has expired, making the connection untrusted.",
                evidence=f"Certificate expired: {ssl_data.get('not_after', 'unknown')}",
                recommendation="Renew the SSL/TLS certificate immediately.",
                cwe="CWE-326",
            ))

        if ssl_data.get("self_signed", False):
            findings.append(Finding(
                title="Self-Signed SSL/TLS Certificate",
                severity="medium",
                description="Self-signed certificates are not trusted by browsers and may indicate test/misconfiguration.",
                evidence="Certificate is self-signed",
                recommendation="Use a certificate from a trusted Certificate Authority (CA).",
            ))

        if ssl_data.get("weak_protocols"):
            findings.append(Finding(
                title="Weak SSL/TLS Protocols Detected",
                severity="high",
                description=f"Weak protocols detected: {', '.join(ssl_data['weak_protocols'])}",
                evidence=f"Protocols: {ssl_data.get('protocols', [])}",
                recommendation="Disable SSLv2, SSLv3, TLSv1.0, and TLSv1.1. Use TLSv1.2 or TLSv1.3.",
                cwe="CWE-327",
            ))

        return findings

    def _calculate_risk_level(self, counts: Dict[str, int]) -> str:
        """Calculate overall risk level."""
        if counts["critical"] > 0:
            return "CRITICAL"
        elif counts["high"] > 0:
            return "HIGH"
        elif counts["medium"] > 2:
            return "MEDIUM"
        elif counts["medium"] > 0 or counts["low"] > 3:
            return "LOW"
        return "INFO"

    def _calculate_score(self, counts: Dict[str, int]) -> float:
        """Calculate numeric security score (0-100, higher is worse)."""
        weights = {"critical": 10.0, "high": 5.0, "medium": 2.0, "low": 0.5, "info": 0.1}
        score = sum(counts.get(sev, 0) * weights[sev] for sev in weights)
        return min(score, 100.0)

    def _generate_summary(self, target: str, counts: Dict[str, int], risk: str) -> str:
        """Generate a human-readable summary."""
        total = sum(counts.values())
        parts = [f"Analysis complete for {target}."]
        if total > 0:
            parts.append(f"Found {total} issue(s):")
            if counts["critical"]:
                parts.append(f"  {counts['critical']} Critical")
            if counts["high"]:
                parts.append(f"  {counts['high']} High")
            if counts["medium"]:
                parts.append(f"  {counts['medium']} Medium")
            if counts["low"]:
                parts.append(f"  {counts['low']} Low")
        else:
            parts.append("No significant issues detected.")
        parts.append(f"Overall risk level: {risk}")
        return "\n".join(parts)