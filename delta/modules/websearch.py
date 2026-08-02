"""

Web Search Module - Web search, CVE lookup, and page fetching capabilities.

Uses DuckDuckGo for privacy-respecting web searches.

"""

import re

import json

import urllib.parse

import urllib.request

from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field

try:

    import requests

    HAS_REQUESTS = True

except ImportError:

    HAS_REQUESTS = False

try:

    from bs4 import BeautifulSoup

    HAS_BS4 = True

except ImportError:

    HAS_BS4 = False

@dataclass

class SearchResult:

    title: str

    url: str

    snippet: str

    source: str = "web"

@dataclass

class WebPageInfo:

    url: str

    title: str

    content: str

    headers: Dict[str, str] = field(default_factory=dict)

    status_code: int = 0

    content_type: str = ""

    error: str = ""

class WebSearchModule:

    def __init__(self, timeout: int = 15):

        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Delta-Security-CLI/1.0"

        self.timeout = timeout

    def search_duckduckgo(self, query: str, max_results: int = 10) -> List[SearchResult]:

        if HAS_REQUESTS and HAS_BS4:

            return self._search_ddg_requests(query, max_results)

        return self._search_ddg_urllib(query, max_results)

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:

        return self.search_duckduckgo(query, max_results)

    def _search_ddg_requests(self, query: str, max_results: int = 10) -> List[SearchResult]:

        try:

            params = {

                "q": query,

                "ia": "web",

                "kl": "us-en",

            }

            headers = {"User-Agent": self.user_agent}

            resp = requests.get(

                "https://html.duckduckgo.com/html/",

                params=params,

                headers=headers,

                timeout=self.timeout,

            )

            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            results = []

            for item in soup.select(".result") or soup.select(".web-result"):

                title_el = item.select_one(".result__title a") or item.select_one("h2 a") or item.select_one("a")

                snippet_el = item.select_one(".result__snippet") or item.select_one(".snippet")

                if title_el:

                    title = title_el.get_text(strip=True)

                    url = title_el.get("href", "")

                    if url and url.startswith("//"):

                        url = "https:" + url

                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    results.append(SearchResult(title=title, url=url, snippet=snippet))

                    if len(results) >= max_results:

                        break

            return results

        except Exception:

            return []

    def _search_ddg_urllib(self, query: str, max_results: int = 10) -> List[SearchResult]:

        try:

            params = urllib.parse.urlencode({"q": query})

            url = f"https://html.duckduckgo.com/html/?{params}"

            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:

                html = resp.read().decode("utf-8", errors="replace")

            results = []

            pattern = r'class="result__title[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'

            snippet_pattern = r'class="result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>'

            title_matches = re.findall(pattern, html, re.DOTALL)

            snippet_matches = re.findall(snippet_pattern, re.DOTALL)

            for i, (url, title) in enumerate(title_matches[:max_results]):

                clean_title = re.sub(r'<[^>]+>', '', title).strip()

                snippet = ""

                if i < len(snippet_matches):

                    snippet = re.sub(r'<[^>]+>', '', snippet_matches[i]).strip()

                if url.startswith("//"):

                    url = "https:" + url

                results.append(SearchResult(title=clean_title, url=url, snippet=snippet))

            return results

        except Exception:

            return []

    def fetch_page(self, url: str) -> WebPageInfo:

        if HAS_REQUESTS:

            return self._fetch_requests(url)

        return self._fetch_urllib(url)

    def _fetch_requests(self, url: str) -> WebPageInfo:

        try:

            headers = {"User-Agent": self.user_agent}

            resp = requests.get(url, headers=headers, timeout=self.timeout)

            content = resp.text[:5000]

            title = ""

            match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)

            if match:

                title = match.group(1).strip()

            return WebPageInfo(

                url=url,

                title=title,

                content=content,

                headers=dict(resp.headers),

                status_code=resp.status_code,

                content_type=resp.headers.get("content-type", ""),

            )

        except Exception as e:

            return WebPageInfo(url=url, title="", content="", error=str(e))

    def _fetch_urllib(self, url: str) -> WebPageInfo:

        try:

            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:

                content = resp.read().decode("utf-8", errors="replace")[:5000]

                headers = dict(resp.headers)

                title = ""

                match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)

                if match:

                    title = match.group(1).strip()

                return WebPageInfo(

                    url=url,

                    title=title,

                    content=content,

                    headers=headers,

                    status_code=resp.status,

                    content_type=resp.headers.get("content-type", ""),

                )

        except Exception as e:

            return WebPageInfo(url=url, title="", content="", error=str(e))

    def search_cve(self, cve_id: str) -> Optional[SearchResult]:

        query = f"{cve_id} vulnerability details"

        results = self.search_duckduckgo(query, max_results=3)

        for r in results:

            if cve_id.lower() in r.title.lower() or cve_id.lower() in r.snippet.lower():

                return r

        return results[0] if results else None

    def search_exploit(self, keyword: str) -> List[SearchResult]:

        query = f"{keyword} exploit"

        return self.search_duckduckgo(query, max_results=5)

    def search_security_news(self, topic: str = "") -> List[SearchResult]:

        query = f"cybersecurity news {topic}".strip()

        return self.search_duckduckgo(query, max_results=5)