# delta/modules/scanner.py
"""
Scanner Module - Core scanning functionality for network, ports, services, and web.
"""

import socket
import ssl
import concurrent.futures
import time
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

from delta.ai.intent import IntentResult
from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager
from delta.ai.knowledge import KnowledgeBase
from delta.ai.reasoning import ReasoningEngine


@dataclass
class ScanResult:
    """Container for scan results."""
    target: str
    ip: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hostname: str = ""
    open_ports: List[Dict] = field(default_factory=list)
    services: Dict[str, Dict] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    ssl_info: Dict[str, Any] = field(default_factory=dict)
    dns_info: Dict[str, Any] = field(default_factory=dict)
    vulnerabilities: List[Dict] = field(default_factory=list)
    risk_level: str = "info"
    summary: str = ""
    scan_duration: float = 0.0


class ScannerModule:
    """
    Comprehensive scanner for network, ports, services, and web applications.
    Uses concurrent threading for fast port scanning.
    """

    def __init__(self, config: DeltaConfig, database: Database,
                 session: SessionManager, display: DisplayManager):
        self.config = config
        self.database = database
        self.session = session
        self.display = display
        self.knowledge = KnowledgeBase(database)
        self.reasoning = ReasoningEngine(self.knowledge)

    def scan(self, target: str, intent: IntentResult = None) -> Optional[Dict[str, Any]]:
        """Execute a comprehensive scan on the target."""
        start_time = time.time()
        target = target or self.session.get_host()
        if not target:
            self.display.error("No target specified")
            return None

        self.display.section(f"🔍 Scanning: {target}")

        result = ScanResult(target=target, ip="")

        step = 0
        for _ in self.display.progress([1, 2, 3, 4, 5], "Scanning..."):
            step += 1
            if step == 1:
                # Step 1: Host resolution
                self.display.info(f"[1/5] Resolving host...")
                result.ip, result.hostname = self._resolve_host(target)
            elif step == 2:
                # Step 2: Port scan
                self.display.info(f"[2/5] Scanning ports...")
                result.open_ports = self._scan_ports(result.ip)
            elif step == 3:
                # Step 3: Service detection
                self.display.info(f"[3/5] Detecting services...")
                result.services = self._detect_services(result.ip, result.open_ports)
            elif step == 4:
                # Step 4: HTTP analysis
                self.display.info(f"[4/5] Analyzing HTTP...")
                if self._has_web_service(result.open_ports):
                    result.headers = self._analyze_http(target)
                    result.ssl_info = self._check_ssl(target)
            elif step == 5:
                # Step 5: Analysis
                self.display.info(f"[5/5] Analyzing results...")
                analysis = self.reasoning.analyze_scan(target, {
                    "open_ports": result.open_ports,
                    "services": result.services,
                    "headers": result.headers,
                    "ssl": result.ssl_info,
                })
                result.risk_level = analysis.risk_level
                result.summary = analysis.summary
                result.vulnerabilities = [
                    {"title": f.title, "severity": f.severity, "description": f.description}
                    for f in analysis.findings
                ]

        result.scan_duration = time.time() - start_time
        
        # Display results
        self._display_scan_results(result, analysis)
        
        # Save to database
        self.database.upsert_host(
            host=target,
            ip=result.ip,
            hostname=result.hostname,
            open_ports=", ".join(str(p["port"]) for p in result.open_ports),
            services=", ".join(result.services.keys()),
            risk_level=result.risk_level,
        )
        
        return {
            "target": target,
            "ip": result.ip,
            "hostname": result.hostname,
            "open_ports": result.open_ports,
            "services": result.services,
            "headers": result.headers,
            "ssl": result.ssl_info,
            "vulnerabilities": result.vulnerabilities,
            "risk_level": result.risk_level,
            "summary": result.summary,
            "duration": result.scan_duration,
            "timestamp": result.timestamp,
        }

    def full_audit(self, target: str, intent: IntentResult = None) -> Optional[Dict[str, Any]]:
        """Execute a full security audit on the target."""
        self.display.section(f"🛡 Full Security Audit: {target}")
        
        # Run comprehensive scan
        scan_result = self.scan(target, intent)
        if not scan_result:
            return None
        
        self.display.success(f"Full audit completed in {scan_result.get('duration', 0):.2f}s")
        return scan_result

    def _resolve_host(self, target: str) -> Tuple[str, str]:
        """Resolve hostname to IP and vice versa."""
        ip = ""
        hostname = ""
        try:
            # Check if target is IP
            try:
                socket.inet_aton(target)
                ip = target
                hostname = socket.getfqdn(target)
                if hostname == target:
                    try:
                        hostname, _, _ = socket.gethostbyaddr(target)
                    except (socket.herror, socket.gaierror):
                        pass
            except socket.error:
                # Target is hostname
                ip = socket.gethostbyname(target)
                hostname = target
        except socket.gaierror:
            self.display.warning(f"Cannot resolve: {target}")
            ip = target
            hostname = target
        
        return ip, hostname

    def _scan_ports(self, ip: str) -> List[Dict]:
        """Scan common ports using concurrent threads."""
        open_ports = []
        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
            1433, 1521, 2049, 3306, 3389, 5432, 5900, 5985, 5986, 6379, 8080,
            8443, 9000, 9090, 10000, 11211, 27017, 50070,
        ]

        def check_port(port: int) -> Optional[int]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.5)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    return port
            except:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(check_port, port): port for port in common_ports}
            for future in concurrent.futures.as_completed(futures):
                port = future.result()
                if port:
                    service = self._get_service_name(port)
                    open_ports.append({"port": port, "service": service, "state": "open"})

        open_ports.sort(key=lambda x: x["port"])
        return open_ports

    def _get_service_name(self, port: int) -> str:
        """Get common service name for a port."""
        services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 111: "RPC", 135: "MSRPC", 139: "NetBIOS",
            143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
            1433: "MSSQL", 1521: "Oracle", 2049: "NFS", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 5985: "WinRM-HTTP",
            5986: "WinRM-HTTPS", 6379: "Redis", 8080: "HTTP-Proxy",
            8443: "HTTPS-Alt", 9000: "PHP-FPM", 9090: "WebLogic",
            10000: "Webmin", 11211: "Memcached", 27017: "MongoDB",
            50070: "Hadoop-NameNode",
        }
        return services.get(port, f"port-{port}")

    def _detect_services(self, ip: str, ports: List[Dict]) -> Dict[str, Dict]:
        """Detect service versions on open ports using banner grabbing."""
        services = {}
        
        for port_info in ports:
            port = port_info["port"]
            banner = self._grab_banner(ip, port)
            if banner:
                service_name = port_info["service"]
                services[service_name] = {
                    "port": port,
                    "banner": banner,
                    "version": self._extract_version(banner),
                }
        
        return services

    def _grab_banner(self, ip: str, port: int, timeout: float = 2.0) -> str:
        """Grab service banner from a port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            # Send probe for common services
            if port in [80, 8080, 443, 8443]:
                sock.send(b"GET / HTTP/1.0\r\n\r\n")
            elif port in [21]:
                pass  # FTP sends banner on connect
            elif port in [22]:
                pass  # SSH sends banner on connect
            elif port in [25]:
                sock.send(b"EHLO scan\r\n")
            elif port in [110]:
                sock.send(b"CAPA\r\n")
            
            try:
                banner = sock.recv(1024).decode("utf-8", errors="ignore").strip()
                sock.close()
                if banner:
                    return banner[:200]
            except:
                sock.close()
        except:
            pass
        
        return ""

    def _extract_version(self, banner: str) -> str:
        """Extract version information from banner."""
        patterns = [
            r'(\d+\.\d+(?:\.\d+)?(?:\.[a-zA-Z0-9]+)?)',
            r'(?:Server|server):\s*([^\r\n]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, banner)
            if match:
                return match.group(1)
        return "unknown"

    def _has_web_service(self, ports: List[Dict]) -> bool:
        """Check if any web services are open."""
        web_ports = {80, 443, 8080, 8443}
        return any(p["port"] in web_ports for p in ports)

    def _analyze_http(self, target: str) -> Dict[str, str]:
        """Analyze HTTP security headers."""
        headers = {}
        
        for scheme, port in [("http", 80), ("https", 443)]:
            url = f"{scheme}://{target}:{port}"
            try:
                req = Request(url, method="GET", headers={"User-Agent": "Delta-Scanner/1.0"})
                with urlopen(req, timeout=5) as resp:
                    for key, value in resp.headers.items():
                        headers[key] = value
                    break
            except URLError:
                continue
            except Exception:
                continue
        
        return headers

    def _check_ssl(self, target: str) -> Dict[str, Any]:
        """Check SSL/TLS certificate information."""
        ssl_info = {}
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((target, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=target) as ssock:
                    cert = ssock.getpeercert()
                    if cert:
                        ssl_info = {
                            "subject": dict(cert.get("subject", [])),
                            "issuer": dict(cert.get("issuer", [])),
                            "version": cert.get("version", ""),
                            "not_before": cert.get("notBefore", ""),
                            "not_after": cert.get("notAfter", ""),
                            "serial": cert.get("serialNumber", ""),
                            "algorithm": cert.get("signatureAlgorithm", ""),
                        }
                        
                        # Check expiration
                        from datetime import datetime as dt
                        not_after = cert.get("notAfter", "")
                        if not_after:
                            try:
                                expiry = dt.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                                ssl_info["expired"] = expiry < dt.now()
                            except:
                                ssl_info["expired"] = False
                        
                        # Detect protocols
                        version = ssock.version()
                        ssl_info["protocol"] = version
                        weak_protocols = []
                        if version in ["SSLv2", "SSLv3", "TLSv1", "TLSv1.1"]:
                            weak_protocols.append(version)
                        ssl_info["weak_protocols"] = weak_protocols
                        
        except Exception as e:
            ssl_info["error"] = str(e)
        
        return ssl_info

    # delta/modules/scanner.py (continued)

    def _display_scan_results(self, result: ScanResult, analysis: Any) -> None:
        """Display scan results in formatted output."""
        # Target info panel
        target_info = (
            f"Target: {result.target}\n"
            f"IP Address: {result.ip}\n"
            f"Hostname: {result.hostname}\n"
            f"Scan Duration: {result.scan_duration:.2f}s\n"
            f"Risk Level: {result.risk_level.upper()}"
        )
        self.display.panel("Target Information", target_info)

        # Open ports table
        if result.open_ports:
            self.display.table(
                "Open Ports",
                ["Port", "Service", "State"],
                [[str(p["port"]), p["service"], p["state"]] for p in result.open_ports]
            )
        else:
            self.display.info("No open ports found on common ports")

        # Services
        if result.services:
            svc_data = []
            for svc_name, svc_info in result.services.items():
                svc_data.append([svc_name, str(svc_info["port"]), svc_info.get("version", "unknown")])
            self.display.table("Detected Services", ["Service", "Port", "Version"], svc_data)

        # Vulnerabilities
        if result.vulnerabilities:
            self.display.section("⚠ Vulnerabilities Found")
            sev_colors = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "cyan"}
            for vuln in result.vulnerabilities:
                color = sev_colors.get(vuln["severity"].lower(), "white")
                self.display.print(f"  [{vuln['severity'].upper()}] {vuln['title']}", style=color)

        # Summary
        self.display.section("Analysis Summary")
        self.display.print(result.summary)