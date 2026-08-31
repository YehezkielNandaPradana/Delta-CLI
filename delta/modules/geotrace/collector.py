"""
GeoTrace Collector Module.
Responsible for collecting and normalizing publicly available OSINT data from social platforms
(GitHub, Telegram, TikTok, Instagram, Twitter/X, and Web Search Engine Footprints).
Strictly adheres to public-only open web reconnaissance without login requirements.
"""

import json
import re
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MediaMetadata:
    media_url: str
    media_type: str = "image"  # "image" | "video"
    has_exif: bool = False
    exif_gps_lat: Optional[float] = None
    exif_gps_lon: Optional[float] = None
    exif_altitude: Optional[float] = None
    exif_timestamp: Optional[str] = None
    exif_camera_make: Optional[str] = None
    exif_camera_model: Optional[str] = None
    visual_clues: List[str] = field(default_factory=list)


@dataclass
class PublicPostData:
    post_id: str
    timestamp_utc: str
    caption_text: str = ""
    explicit_geotag: Optional[str] = None
    geotag_lat: Optional[float] = None
    geotag_lon: Optional[float] = None
    media_items: List[MediaMetadata] = field(default_factory=list)
    language_code: Optional[str] = None


@dataclass
class PublicProfileData:
    handle: str
    platform: str
    profile_url: str
    display_name: str = ""
    bio: str = ""
    links: List[str] = field(default_factory=list)
    is_private: bool = False
    posts: List[PublicPostData] = field(default_factory=list)
    raw_attributes: Dict[str, Any] = field(default_factory=dict)


class PublicDataCollector:
    """
    Collector for public social media OSINT footprint.
    Normalizes handles, probes open public endpoints, extracts real live metadata.
    """

    PLATFORM_PATTERNS = {
        "facebook": r"(?:https?://(?:www\.)?facebook\.com/)?@?([A-Za-z0-9_.\-]{1,50})",
        "instagram": r"(?:https?://(?:www\.)?instagram\.com/)?@?([A-Za-z0-9_.\-]{1,30})",
        "tiktok": r"(?:https?://(?:www\.)?tiktok\.com/@)?@?([A-Za-z0-9_.\-]{1,30})",
        "x": r"(?:https?://(?:www\.)?(?:twitter\.com|x\.com)/)?@?([A-Za-z0-9_]{1,15})",
        "threads": r"(?:https?://(?:www\.)?threads\.net/@)?@?([A-Za-z0-9_.\-]{1,30})",
        "bluesky": r"(?:https?://(?:www\.)?bsky\.app/profile/)?@?([A-Za-z0-9_.\-]+\.[a-z]{2,})",
        "generic": r"^@?([A-Za-z0-9_.\-]{1,50})$"
    }

    def normalize_input(self, target_input: str) -> Tuple[str, str, str]:
        """
        Extract (platform, clean_handle, canonical_url) from handle or URL.
        """
        raw = target_input.strip()

        # 1. Clean URL to handle
        clean = raw.split("?")[0].split("#")[0].rstrip("/")
        if "/" in clean:
            clean = clean.split("/")[-1]
        clean_handle = clean.lstrip("@")

        platform = "generic"
        if "twitter.com" in raw or "x.com" in raw:
            platform = "x"
        elif "facebook.com" in raw:
            platform = "facebook"
        elif "instagram.com" in raw:
            platform = "instagram"
        elif "tiktok.com" in raw:
            platform = "tiktok"
        elif "threads.net" in raw:
            platform = "threads"
        elif "bsky.app" in raw:
            platform = "bluesky"

        canonical_url = raw if "http" in raw else f"https://{platform if platform != 'generic' else 'social'}.com/{clean_handle}"
        return platform, clean_handle, canonical_url

    def parse_exif_gps(self, exif_dict: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """
        Convert EXIF GPS coordinates (DMS or Decimal) into standard decimal degrees.
        """
        if not exif_dict:
            return None, None

        def dms_to_deg(dms, ref):
            if isinstance(dms, (int, float)):
                deg = float(dms)
            elif isinstance(dms, (list, tuple)) and len(dms) == 3:
                deg = float(dms[0]) + float(dms[1]) / 60.0 + float(dms[2]) / 3600.0
            else:
                return None
            if ref in ("S", "W", "s", "w"):
                deg = -deg
            return deg

        lat = None
        lon = None

        if "GPSLatitude" in exif_dict and "GPSLatitudeRef" in exif_dict:
            lat = dms_to_deg(exif_dict["GPSLatitude"], exif_dict["GPSLatitudeRef"])
        elif "lat" in exif_dict:
            lat = float(exif_dict["lat"])

        if "GPSLongitude" in exif_dict and "GPSLongitudeRef" in exif_dict:
            lon = dms_to_deg(exif_dict["GPSLongitude"], exif_dict["GPSLongitudeRef"])
        elif "lon" in exif_dict:
            lon = float(exif_dict["lon"])

        return lat, lon

    def _probe_live_footprints(self, handle: str) -> Dict[str, Any]:
        """
        Live probes against open metadata endpoints across platforms:
        - GitHub API
        - Telegram Public Preview
        - DuckDuckGo / Open Search Engine Entity Graph
        - Public Web Profile meta tags
        """
        findings = {"snippets": [], "links": [], "posts": [], "geo_clues": [], "display_name": "", "bio": ""}
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 1. Probe GitHub Open Public API
        try:
            req = urllib.request.Request(
                f"https://api.github.com/users/{handle}",
                headers={"User-Agent": "DeltaOSINT-Live-Collector/3.0"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    if data.get("name"):
                        findings["display_name"] = data["name"]
                    if data.get("location"):
                        findings["geo_clues"].append(data["location"])
                        findings["snippets"].append(f"GitHub location: {data['location']}")
                    if data.get("bio"):
                        findings["bio"] = data["bio"]
                        findings["snippets"].append(f"GitHub bio: {data['bio']}")
                    if data.get("company"):
                        findings["snippets"].append(f"GitHub organization: {data['company']}")
                    findings["links"].append(data.get("html_url", f"https://github.com/{handle}"))
        except Exception:
            pass

        # 2. Probe Telegram Public Channel/Profile Preview
        try:
            req = urllib.request.Request(
                f"https://t.me/s/{handle}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
                if resp.status == 200:
                    html = resp.read().decode("utf-8", errors="ignore")
                    title_m = re.search(r'<meta property="og:title" content="([^"]*)"', html)
                    desc_m = re.search(r'<meta property="og:description" content="([^"]*)"', html)
                    if title_m:
                        t_text = title_m.group(1).replace("Telegram: Contact ", "").replace("@", "").strip()
                        if not findings["display_name"]:
                            findings["display_name"] = t_text
                        findings["snippets"].append(f"Telegram profile: {t_text}")
                        findings["links"].append(f"https://t.me/{handle}")
                    if desc_m and desc_m.group(1):
                        t_desc = desc_m.group(1).strip()
                        if not findings["bio"]:
                            findings["bio"] = t_desc
                        findings["snippets"].append(f"Telegram description: {t_desc}")
        except Exception:
            pass

        # 3. Probe DuckDuckGo Instant Open Search API for Public Entity Disambiguation
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(handle)}&format=json&no_html=1"
            req = urllib.request.Request(
                ddg_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    if data.get("Heading"):
                        findings["snippets"].append(f"Entity: {data['Heading']}")
                    if data.get("AbstractText"):
                        findings["snippets"].append(data["AbstractText"])
                    if data.get("AbstractURL"):
                        findings["links"].append(data["AbstractURL"])
        except Exception:
            pass

        # 4. Search Query Expansion for Social Footprints
        clean_query = handle.replace(".", " ").replace("_", " ").replace("-", " ").strip()
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=chrome&q={urllib.parse.quote(clean_query)}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if len(data) > 1 and isinstance(data[1], list):
                    for sug in data[1][:3]:
                        findings["snippets"].append(f"Public entity search footprint: {sug}")
        except Exception:
            pass

        # Common public profile reference URLs
        social_targets = [
            f"https://www.instagram.com/{handle}/",
            f"https://www.tiktok.com/@{handle}",
            f"https://twitter.com/{handle}",
            f"https://facebook.com/{handle}"
        ]
        for st in social_targets:
            if st not in findings["links"]:
                findings["links"].append(st)

        return findings

    def collect_public_profile(self, target: str) -> PublicProfileData:
        """
        Fetch public OSINT footprint dynamically from open web search & profile parsing.
        """
        platform, clean_handle, canonical_url = self.normalize_input(target)

        # Live probe footprints
        live_data = self._probe_live_footprints(clean_handle)
        bio_snippets = live_data["snippets"]
        links = live_data["links"]
        display_name = live_data.get("display_name") or clean_handle.capitalize()
        bio_text = live_data.get("bio") or (" | ".join(bio_snippets) if bio_snippets else f"Public profile @{clean_handle}")

        # Real collected posts / geo clues
        posts_data = []
        for idx, clue in enumerate(live_data.get("geo_clues", [])):
            posts_data.append(PublicPostData(
                post_id=f"live-clue-{idx+1}",
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                caption_text=clue,
                explicit_geotag=clue,
                media_items=[],
                language_code=None
            ))

        return PublicProfileData(
            handle=clean_handle,
            platform=platform,
            profile_url=canonical_url,
            display_name=display_name,
            bio=bio_text,
            links=links,
            is_private=False,
            posts=posts_data
        )

    def build_mock_profile_for_testing(
        self,
        handle: str,
        bio: str = "Photographer based in Jakarta & Bandung. Exploring coffee shops.",
        is_private: bool = False,
        posts: Optional[List[Dict[str, Any]]] = None
    ) -> PublicProfileData:
        """
        Helper for unit tests and local mock analysis.
        """
        platform, clean_handle, url = self.normalize_input(handle)

        post_objects = []
        if posts:
            for p in posts:
                media_list = []
                for m in p.get("media", []):
                    media_list.append(MediaMetadata(
                        media_url=m.get("url", ""),
                        media_type=m.get("type", "image"),
                        has_exif=bool(m.get("exif")),
                        exif_gps_lat=m.get("exif", {}).get("lat"),
                        exif_gps_lon=m.get("exif", {}).get("lon"),
                        exif_timestamp=m.get("exif", {}).get("timestamp"),
                        exif_camera_make=m.get("exif", {}).get("make"),
                        exif_camera_model=m.get("exif", {}).get("model"),
                        visual_clues=m.get("visual_clues", [])
                    ))

                post_objects.append(PublicPostData(
                    post_id=p.get("post_id", "post-001"),
                    timestamp_utc=p.get("timestamp_utc", datetime.now(timezone.utc).isoformat()),
                    caption_text=p.get("caption", ""),
                    explicit_geotag=p.get("geotag"),
                    geotag_lat=p.get("geotag_lat"),
                    geotag_lon=p.get("geotag_lon"),
                    media_items=media_list,
                    language_code=p.get("language_code", "id")
                ))

        return PublicProfileData(
            handle=clean_handle,
            platform=platform,
            profile_url=url,
            display_name=clean_handle.capitalize(),
            bio=bio,
            is_private=is_private,
            posts=post_objects
        )
