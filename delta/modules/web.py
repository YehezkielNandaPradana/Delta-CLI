# delta/modules/web.py
"""
Web Analysis Module - HTTP header analysis, security checks, and technology detection.
"""

import socket
import ssl
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser


@dataclass
class WebAnalysisResult:
    """Web application analysis result."""
    url: str
    status_code: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    server: str = ""
    technologies: List[str] = field(default_factory=list)
    security_headers: Dict[str, bool] = field(default_factory=dict)
    cookies: List[Dict] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    title: str = ""
    robots_txt: str = ""
    sitemap: str = ""


class WebModule:
    """
    Web application security analysis module.
    Analyzes HTTP headers, security configurations, and technology stack.
    """

    def analyze(self, target: str, port: int = 80) -> WebAnalysisResult:
        """Analyze a web application."""
        # Try HTTPS first, then HTTP
        for scheme, check_port in [("https", 443), ("http", 80)]:
            url = f"{scheme}://{target}:{check_port}"
            result = self._analyze_url(url)
            if result.status_code:
                return result
        
        # Try with default ports
        for scheme in ["https", "http"]:
            url = f"{scheme}://{target}"
            result = self._analyze_url(url)
            if result.status_code:
                return result
        
        return WebAnalysisResult(url=f"http://{target}")

    USER_AGENTS = [
        "Mozilla/5.0 (compatible; Delta-Scanner/1.0)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/120.0",
        "Delta-CLI/1.0 (+https://github.com/YehezkielNandaPradana/Delta-CLI)",
    ]

    def _get_user_agent(self) -> str:
        """Rotate through user agents."""
        import random
        return random.choice(self.USER_AGENTS)

    def _analyze_url(self, url: str) -> WebAnalysisResult:
        """Analyze a single URL."""
        result = WebAnalysisResult(url=url)
        
        try:
            req = Request(url, method="GET", headers={
                "User-Agent": self._get_user_agent(),
                "Accept": "text/html,application/xhtml+xml",
            })
            
            with urlopen(req, timeout=10) as resp:
                result.status_code = resp.status
                
                # Headers
                for key, value in resp.headers.items():
                    result.headers[key] = value
                
                # Server
                result.server = resp.headers.get("Server", "")
                
                # Security headers check
                security_checks = {
                    "Strict-Transport-Security": "strict-transport-security",
                    "X-Frame-Options": "x-frame-options",
                    "X-Content-Type-Options": "x-content-type-options",
                    "Content-Security-Policy": "content-security-policy",
                    "X-XSS-Protection": "x-xss-protection",
                    "Referrer-Policy": "referrer-policy",
                    "Permissions-Policy": "permissions-policy",
                }
                for display_name, key in security_checks.items():
                    result.security_headers[display_name] = key in {k.lower(): v for k, v in resp.headers.items()}
                
                # Detect technologies
                result.technologies = self._detect_technologies(resp.headers, resp.read(8192).decode("utf-8", errors="ignore"))
                
        except HTTPError as e:
            result.status_code = e.code
            for key, value in e.headers.items():
                result.headers[key] = value
        except URLError:
            pass
        except Exception:
            pass
        
        return result

    def _detect_technologies(self, headers: Dict[str, str], body: str) -> List[str]:
        """Detect web technologies from headers and HTML."""
        technologies = set()
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # Server detection
        server = headers_lower.get("server", "").lower()
        if "apache" in server:
            technologies.add("Apache HTTP Server")
        if "nginx" in server:
            technologies.add("nginx")
        if "iis" in server:
            technologies.add("IIS")
        if "cloudflare" in server:
            technologies.add("Cloudflare")
        
        # X-Powered-By
        powered = headers_lower.get("x-powered-by", "").lower()
        if "php" in powered:
            technologies.add("PHP")
        if "asp.net" in powered or "aspnet" in powered:
            technologies.add("ASP.NET")
        if "express" in powered:
            technologies.add("Express.js")
        
        # Set-Cookie analysis
        set_cookie = headers_lower.get("set-cookie", "").lower()
        if "phpsessid" in set_cookie:
            technologies.add("PHP Session")
        if "aspsessionid" in set_cookie or "asp.net_sessionid" in set_cookie:
            technologies.add("ASP.NET Session")
        if "jsessionid" in set_cookie:
            technologies.add("Java JSP")
        
        # Body patterns
        body_lower = body.lower()
        if "wordpress" in body_lower or "wp-content" in body_lower or "wp-includes" in body_lower:
            technologies.add("WordPress")
        if "drupal" in body_lower or "/sites/default/" in body_lower:
            technologies.add("Drupal")
        if "joomla" in body_lower or "/components/" in body_lower:
            technologies.add("Joomla")
        if "jquery" in body_lower:
            technologies.add("jQuery")
        if "react" in body_lower or "reactdom" in body_lower or "reactroot" in body_lower:
            technologies.add("React")
        if "vue" in body_lower or "vuejs" in body_lower:
            technologies.add("Vue.js")
        if "angular" in body_lower or "ng-app" in body_lower or "ng-version" in body_lower:
            technologies.add("Angular")
        if "laravel" in body_lower or "csrf-token" in body_lower:
            technologies.add("Laravel")
        if "bootstrap" in body_lower:
            technologies.add("Bootstrap")
        
        return sorted(technologies)

    def check_https_redirect(self, target: str) -> bool:
        """Check if HTTP redirects to HTTPS."""
        try:
            http_url = f"http://{target}"
            req = Request(http_url, method="HEAD", headers={"User-Agent": "Delta/1.0"})
            
            import http.client
            conn = http.client.HTTPConnection(target, timeout=5)
            conn.request("HEAD", "/")
            resp = conn.getresponse()
            
            return resp.status in [301, 302, 307, 308] and "location" in {k.lower(): k for k, v in resp.headers.items()}
        except:
            return False

    def check_security_headers(self, target: str) -> Dict[str, bool]:
        """Check for presence of security headers."""
        security_headers = {
            "strict-transport-security": False,
            "x-frame-options": False,
            "x-content-type-options": False,
            "content-security-policy": False,
            "x-xss-protection": False,
            "referrer-policy": False,
            "permissions-policy": False,
        }
        
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{target}"
                req = Request(url, method="HEAD", headers={"User-Agent": "Delta/1.0"})
                with urlopen(req, timeout=5) as resp:
                    headers_lower = {k.lower(): v for k, v in resp.headers.items()}
                    for header in security_headers:
                        if header in headers_lower:
                            security_headers[header] = True
                    break
            except:
                continue
        
        return security_headers

    def extract_title(self, target: str) -> str:
        """Extract page title from target."""
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{target}"
                req = Request(url, method="GET", headers={"User-Agent": "Delta/1.0"})
                with urlopen(req, timeout=10) as resp:
                    html = resp.read(16384).decode("utf-8", errors="ignore")
                    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                    return ""
            except:
                continue
        return ""

    def check_cookies(self, target: str) -> List[Dict[str, Any]]:
        """Analyze cookies for security flags."""
        cookies = []
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{target}"
                req = Request(url, method="HEAD", headers={"User-Agent": "Delta/1.0"})
                with urlopen(req, timeout=5) as resp:
                    for cookie in resp.headers.get_all("Set-Cookie", []):
                        cookie_info = {"value": cookie, "secure": False, "httponly": False, "samesite": None}
                        if "secure" in cookie.lower():
                            cookie_info["secure"] = True
                        if "httponly" in cookie.lower():
                            cookie_info["httponly"] = True
                        samesite_match = re.search(r"samesite=([^;]+)", cookie, re.IGNORECASE)
                        if samesite_match:
                            cookie_info["samesite"] = samesite_match.group(1)
                        cookies.append(cookie_info)
                    break
            except:
                continue
        return cookies

    def check_robots_txt(self, target: str) -> Dict[str, Any]:
        """Check robots.txt for sensitive paths."""
        result = {"exists": False, "disallowed": [], "sitemaps": []}
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{target}/robots.txt"
                req = Request(url, method="GET", headers={"User-Agent": "Delta/1.0"})
                with urlopen(req, timeout=5) as resp:
                    result["exists"] = True
                    content = resp.read().decode("utf-8", errors="ignore")
                    for line in content.split("\n"):
                        line = line.lower().strip()
                        if line.startswith("disallow:"):
                            path = line.split(":", 1)[1].strip()
                            if path and path != "/":
                                result["disallowed"].append(path)
                        elif line.startswith("sitemap:"):
                            result["sitemaps"].append(line.split(":", 1)[1].strip())
                    break
            except:
                continue
        return result
    def check_common_files(self, target: str, paths: List[str] = None) -> List[Dict[str, Any]]:
        """Check for common sensitive files."""
        if paths is None:
            paths = [
                "/.git/config", "/.env", "/config.php", "/wp-config.php",
                "/admin/config.php", "/backup.zip", "/backup.sql", "/db.sql",
                "/phpinfo.php", "/.htaccess", "/.htpasswd", "/server-status",
                "/server-info", "/elmah.axd", "/trace.axd",
            ]

        results = []
        for scheme in ["https", "http"]:
            if results:
                break
            for path in paths:
                try:
                    url = f"{scheme}://{target}{path}"
                    req = Request(url, method="HEAD", headers={"User-Agent": "Delta/1.0"})
                    with urlopen(req, timeout=5) as resp:
                        results.append({
                            "path": path,
                            "status": resp.status,
                            "exists": True,
                            "sensitive": path in ["/.git/config", "/.env", "/backup.sql", "/backup.zip"]
                        })
                except:
                    pass
        return results

    def check_http_methods(self, target: str) -> List[str]:
        """Check allowed HTTP methods."""
        allowed = []
        for scheme in ["https", "http"]:
            try:
                url = f"{scheme}://{target}"
                req = Request(url, method="OPTIONS", headers={"User-Agent": "Delta/1.0"})
                with urlopen(req, timeout=5) as resp:
                    allow = resp.headers.get("Allow", "")
                    allowed = [m.strip() for m in allow.split(",") if m.strip()]
                    break
            except:
                continue
        return allowed

    def find_directories(self, target: str, wordlist: List[str] = None) -> List[Dict[str, Any]]:
        """Basic directory enumeration."""
        if wordlist is None:
            wordlist = ["admin", "login", "wp-admin", "administrator", "backup", 
                       "config", "uploads", "images", "css", "js", "api", "v1", "v2"]

        results = []
        for scheme in ["https", "http"]:
            if results:
                break
            for path in wordlist:
                try:
                    url = f"{scheme}://{target}/{path}"
                    req = Request(url, method="GET", headers={"User-Agent": "Delta/1.0"})
                    with urlopen(req, timeout=5) as resp:
                        results.append({
                            "path": f"/{path}",
                            "status": resp.status,
                        })
                except:
                    pass
        return results
