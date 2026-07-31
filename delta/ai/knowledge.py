# delta/ai/knowledge.py
"""
Knowledge Base for Delta - stores vulnerability data, security concepts, and remediation advice.
""" 

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VulnerabilityInfo:
    """Information about a known vulnerability."""
    id: str
    name: str
    category: str
    severity: str  # critical, high, medium, low, info
    description: str
    impact: str
    possible_cause: str
    recommendation: str
    references: List[str] = field(default_factory=list)
    cwe: str = ""
    owasp_category: str = ""


@dataclass
class SecurityConcept:
    """Information about a security concept."""
    name: str
    description: str
    category: str
    best_practice: str
    references: List[str] = field(default_factory=list)


class KnowledgeBase:
    """
    Built-in security knowledge base.
    Contains vulnerability definitions, remediation advice, and security concepts.
    All data is stored locally - no internet required.
    """

    def __init__(self, database: Any = None):
        self.database = database
        self._vulnerabilities: Dict[str, VulnerabilityInfo] = {}
        self._concepts: Dict[str, SecurityConcept] = {}
        self._init_vulnerabilities()
        self._init_concepts()

    @property
    def vulnerability_count(self) -> int:
        return len(self._vulnerabilities)

    @property
    def concept_count(self) -> int:
        return len(self._concepts)

    def _init_vulnerabilities(self) -> None:
        """Initialize vulnerability knowledge base."""
        vulns = [
            VulnerabilityInfo(
                id="SQLI",
                name="SQL Injection",
                category="Injection",
                severity="critical",
                description="SQL Injection occurs when untrusted user input is embedded directly into SQL queries without proper sanitization or parameterization. This allows attackers to manipulate database queries, potentially extracting, modifying, or deleting sensitive data.",
                impact="An attacker can read, modify, or delete arbitrary data from the database. In severe cases, complete database compromise, operating system command execution, or full server takeover is possible.",
                possible_cause="Application uses string concatenation to build SQL queries with user input. Lack of prepared statements, parameterized queries, or proper input validation.",
                recommendation="Use parameterized queries/prepared statements. Implement strict input validation. Use an ORM framework. Apply least privilege principle to database accounts. Conduct regular code reviews and penetration testing.",
                references=["OWASP SQL Injection", "CWE-89", "https://owasp.org/www-community/attacks/SQL_Injection"],
                cwe="CWE-89",
                owasp_category="A03:2021 - Injection",
            ),
            VulnerabilityInfo(
                id="XSS",
                name="Cross-Site Scripting (XSS)",
                category="Injection",
                severity="high",
                description="Cross-Site Scripting (XSS) allows attackers to inject malicious scripts into web pages viewed by other users. This occurs when untrusted data is included in web page output without proper encoding or validation.",
                impact="Attackers can steal session cookies, redirect users to malicious sites, deface websites, capture keystrokes, or perform actions on behalf of the victim.",
                possible_cause="User input is reflected in web pages without proper encoding. Dynamic content generation without context-aware output encoding. Missing Content-Security-Policy headers.",
                recommendation="Implement context-aware output encoding. Use Content-Security-Policy headers. Validate and sanitize all user inputs. Use secure frameworks with auto-escaping. Regular security testing.",
                references=["OWASP XSS", "CWE-79", "https://owasp.org/www-community/attacks/xss/"],
                cwe="CWE-79",
                owasp_category="A03:2021 - Injection",
            ),
            VulnerabilityInfo(
                id="OPEN_PORT",
                name="Open Network Port",
                category="Network Security",
                severity="medium",
                description="Unnecessary open ports expose network services to potential exploitation. Each open port represents a potential attack vector that can be used to compromise the system.",
                impact="Increased attack surface. Potential unauthorized access, data exfiltration, or service exploitation depends on the service running on the open port.",
                possible_cause="Default configurations with unnecessary services enabled. Lack of proper firewall rules. Misconfigured network segmentation.",
                recommendation="Close all unnecessary ports. Implement firewall rules to restrict access. Use principle of least functionality. Regular port audits. Network segmentation.",
                references=["OWASP Network Security", "CIS Benchmarks"],
                cwe="CWE-200",
                owasp_category="A05:2021 - Security Misconfiguration",
            ),
            VulnerabilityInfo(
                id="WEAK_SSL",
                name="Weak SSL/TLS Configuration",
                category="Cryptographic Failures",
                severity="high",
                description="Outdated or misconfigured SSL/TLS protocols and ciphers expose encrypted communications to interception and decryption attacks.",
                impact="Man-in-the-middle attacks, data interception, session hijacking. Sensitive data transmitted over the connection can be read by attackers.",
                possible_cause="Use of outdated protocols (SSLv2, SSLv3, TLSv1.0). Weak cipher suites. Expired or self-signed certificates. Missing HSTS headers.",
                recommendation="Disable SSLv2, SSLv3, TLSv1.0, TLSv1.1. Use TLSv1.2+ with strong ciphers. Implement HSTS. Use trusted certificates. Regular certificate validation.",
                references=["OWASP Transport Layer Protection", "CWE-327", "https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html"],
                cwe="CWE-327",
                owasp_category="A02:2021 - Cryptographic Failures",
            ),
            VulnerabilityInfo(
                id="MISSING_HEADERS",
                name="Missing Security Headers",
                category="Security Misconfiguration",
                severity="medium",
                description="Web applications missing critical security headers (HSTS, X-Frame-Options, X-Content-Type-Options, Content-Security-Policy) are vulnerable to various attacks.",
                impact="Clickjacking, MIME-type sniffing attacks, XSS amplification, protocol downgrade attacks.",
                possible_cause="Missing security hardening. Default web server configuration. Lack of security awareness.",
                recommendation="Implement HSTS, X-Frame-Options: DENY/SAMEORIGIN, X-Content-Type-Options: nosniff, Content-Security-Policy, X-XSS-Protection, Referrer-Policy headers.",
                references=["OWASP Security Headers", "https://securityheaders.com"],
                cwe="CWE-693",
                owasp_category="A05:2021 - Security Misconfiguration",
            ),
            VulnerabilityInfo(
                id="INFO_DISCLOSURE",
                name="Information Disclosure",
                category="Information Disclosure",
                severity="medium",
                description="Revealing system information through server banners, error messages, directory listings, or exposed configuration files provides attackers with valuable reconnaissance data.",
                impact="Attackers can gather intelligence about the technology stack, version numbers, and potential vulnerabilities to tailor their attacks.",
                possible_cause="Default server banners enabled. Debug mode enabled. Directory listing enabled. Exposed configuration files (.git, .env, backup files). Verbose error messages.",
                recommendation="Disable server banners. Disable directory listing. Remove unnecessary files. Use custom error pages. Implement proper access controls.",
                references=["OWASP Information Disclosure", "CWE-200"],
                cwe="CWE-200",
                owasp_category="A04:2021 - Information Disclosure",
            ),
            VulnerabilityInfo(
                id="WEAK_PASSWORD",
                name="Weak Password Policy",
                category="Authentication",
                severity="high",
                description="Weak or missing password policies allow users to create easily guessable passwords, increasing the risk of account compromise.",
                impact="Account takeover, data breach, unauthorized access to sensitive systems and data.",
                possible_cause="No minimum password length. No complexity requirements. Common passwords allowed. No account lockout. No multi-factor authentication.",
                recommendation="Implement strong password policy (min 12 chars, complexity). Enable MFA. Use account lockout. Consider passwordless authentication. Regular password audits.",
                references=["OWASP Authentication Cheatsheet", "CWE-521", "NIST SP 800-63B"],
                cwe="CWE-521",
                owasp_category="A07:2021 - Identification and Authentication Failures",
            ),
            VulnerabilityInfo(
                id="DIR_TRAVERSAL",
                name="Directory Traversal",
                category="Input Validation",
                severity="high",
                description="Directory traversal allows attackers to access files and directories outside the web root directory by manipulating path variables.",
                impact="Access to sensitive files (passwords, configuration, source code). Potential command execution if combined with file upload functionality.",
                possible_cause="User-supplied file paths not properly validated. Missing access controls. Use of user input in file system operations.",
                recommendation="Validate and sanitize file paths. Use allowlist of permitted files. Use chroot jails. Implement proper access controls. Avoid passing user input to file system APIs.",
                references=["OWASP Path Traversal", "CWE-22"],
                cwe="CWE-22",
                owasp_category="A01:2021 - Broken Access Control",
            ),
            VulnerabilityInfo(
                id="CSRF",
                name="Cross-Site Request Forgery",
                category="Access Control",
                severity="medium",
                description="CSRF tricks authenticated users into executing unwanted actions on web applications where they're currently authenticated, by exploiting the application's trust in the user's browser.",
                impact="Unauthorized actions performed on behalf of authenticated users, such as changing passwords, making transactions, or modifying data.",
                possible_cause="No CSRF tokens. SameSite cookie attribute not set. Actions rely solely on cookies for authentication. No re-authentication for sensitive actions.",
                recommendation="Implement CSRF tokens. Set SameSite=Strict/Lax cookie attribute. Use custom request headers. Implement re-authentication for sensitive actions.",
                references=["OWASP CSRF", "CWE-352"],
                cwe="CWE-352",
                owasp_category="A01:2021 - Broken Access Control",
            ),
        ]

        for vuln in vulns:
            self._vulnerabilities[vuln.id] = vuln
            # Also index by name and category
            self._vulnerabilities[vuln.name.lower()] = vuln

    def _init_concepts(self) -> None:
        """Initialize security concept knowledge."""
        concepts = [
            SecurityConcept(
                name="CVE",
                description="Common Vulnerabilities and Exposures - A dictionary of publicly disclosed cybersecurity vulnerabilities. Each CVE has a unique identifier (CVE-YYYY-NNNNN) and description.",
                category="General",
                best_practice="Regularly check for CVEs affecting your software stack. Use vulnerability scanners and keep systems patched.",
                references=["https://cve.mitre.org", "https://nvd.nist.gov"],
            ),
            SecurityConcept(
                name="CWE",
                description="Common Weakness Enumeration - A taxonomy of common software and hardware weaknesses that can lead to security vulnerabilities.",
                category="General",
                best_practice="Reference CWEs during code review and development to avoid introducing common weaknesses.",
                references=["https://cwe.mitre.org"],
            ),
            SecurityConcept(
                name="OWASP Top 10",
                description="The OWASP Top 10 is a standard awareness document representing a broad consensus about the most critical security risks to web applications.",
                category="Standard",
                best_practice="Use OWASP Top 10 as a baseline for your application security program. Address all categories in your security testing.",
                references=["https://owasp.org/Top10/"],
            ),
            SecurityConcept(
                name="CIS Benchmarks",
                description="Center for Internet Security Benchmarks provide prescriptive guidance for securely configuring systems. Over 100 configuration guidelines across 25+ vendor product families.",
                category="Standard",
                best_practice="Apply CIS benchmarks for all operating systems, cloud services, and applications in your environment.",
                references=["https://www.cisecurity.org/cis-benchmarks/"],
            ),
            SecurityConcept(
                name="CVSS",
                description="Common Vulnerability Scoring System - A free and open industry standard for assessing the severity of computer system security vulnerabilities.",
                category="Standard",
                best_practice="Use CVSS scores to prioritize vulnerability remediation. CVSS v3.1 is the current standard with scores from 0.0 (None) to 10.0 (Critical).",
                references=["https://www.first.org/cvss/"],
            ),
            SecurityConcept(
                name="Principle of Least Privilege",
                description="Security principle where users, processes, and systems are granted the minimum levels of access necessary to perform their functions.",
                category="Principle",
                best_practice="Implement role-based access control. Regularly audit permissions. Remove unused accounts and excessive privileges.",
                references=["NIST SP 800-53"],
            ),
            SecurityConcept(
                name="Defense in Depth",
                description="A cybersecurity strategy using multiple layers of security controls throughout the IT system. If one layer fails, additional layers provide protection.",
                category="Principle",
                best_practice="Implement security at network, host, application, and data layers. Use a combination of preventive, detective, and responsive controls.",
                references=["NIST Cybersecurity Framework"],
            ),
        ]

        for concept in concepts:
            self._concepts[concept.name.lower()] = concept

    def get_vulnerability(self, key: str) -> Optional[VulnerabilityInfo]:
        """Get vulnerability information by ID, name, or keyword."""
        key_lower = key.lower().strip()
        # Direct lookup
        if key_lower in self._vulnerabilities:
            return self._vulnerabilities[key_lower]
        # Search by keyword in name
        for vid, vuln in self._vulnerabilities.items():
            if key_lower in vuln.name.lower() or key_lower in vuln.category.lower():
                return vuln
        return None

    def search_vulnerabilities(self, query: str) -> List[VulnerabilityInfo]:
        """Search vulnerabilities by keyword."""
        query_lower = query.lower().strip()
        results = []
        for vuln in self._vulnerabilities.values():
            if (query_lower in vuln.name.lower() or
                query_lower in vuln.description.lower() or
                query_lower in vuln.category.lower() or
                query_lower in vuln.cwe.lower()):
                if vuln not in results:
                    results.append(vuln)
        return results[:10]  # Limit results

    def get_concept(self, name: str) -> Optional[SecurityConcept]:
        """Get security concept by name."""
        return self._concepts.get(name.lower().strip())

    def search_concepts(self, query: str) -> List[SecurityConcept]:
        """Search concepts by keyword."""
        query_lower = query.lower().strip()
        return [
            c for c in self._concepts.values()
            if query_lower in c.name.lower() or query_lower in c.description.lower()
        ][:10]

    def get_all_vulnerabilities(self) -> List[VulnerabilityInfo]:
        """Get unique vulnerabilities."""
        seen = set()
        unique = []
        for vuln in self._vulnerabilities.values():
            if vuln.id not in seen:
                seen.add(vuln.id)
                unique.append(vuln)
        return unique

    def get_severity_count(self) -> Dict[str, int]:
        """Get count of vulnerabilities by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        seen = set()
        for vuln in self._vulnerabilities.values():
            if vuln.id not in seen:
                seen.add(vuln.id)
                sev = vuln.severity.lower()
                if sev in counts:
                    counts[sev] += 1
        return counts