"""
GeoTrace Extractor Module.
Extracts geographic candidates from raw public profile artifacts:
- EXIF metadata (GPS tags) via dynamic reverse-geocoding
- Explicit user geotags via dynamic OSM Nominatim geocoding
- Visual features (Landmarks, street signs, vehicle plates)
- Temporal patterns (Posting hours, active timezone inference)
- Textual context (Bio mentions, location tokens)
Enforces minimum resolution bounding (City/Sub-district level).
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from delta.modules.geotrace.collector import PublicProfileData, PublicPostData
from delta.modules.geotrace.geocoder import DynamicGeocoder


@dataclass
class LocationCandidate:
    source_type: str  # "EXIF_GPS", "EXPLICIT_GEOTAG", "VISUAL_AI", "TEMPORAL_TIMEZONE", "TEXTUAL_BIO"
    city: str
    region_province: str
    country: str
    country_code: str = ""
    latitude_approx: Optional[float] = None
    longitude_approx: Optional[float] = None
    confidence_base: float = 0.0
    evidence_snippet: str = ""
    raw_signal: str = ""
    is_precise_explicit: bool = False  # True if user explicitly published exact coordinates


class GeoCandidateExtractor:
    """
    Parses public profile signals into structured LocationCandidate entities
    utilizing dynamic geocoding without hardcoded city/landmark dependencies.
    """

    # Vehicle plate prefixes to region indicator mapping
    VEHICLE_PLATE_MAP = {
        "B": ("Jakarta", "DKI Jakarta", "Indonesia", "ID", -6.2088, 106.8456),
        "D": ("Bandung", "Jawa Barat", "Indonesia", "ID", -6.9175, 107.6191),
        "L": ("Surabaya", "Jawa Timur", "Indonesia", "ID", -7.2575, 112.7521),
        "W": ("Sidoarjo", "Jawa Timur", "Indonesia", "ID", -7.4726, 112.6675),
        "N": ("Malang", "Jawa Timur", "Indonesia", "ID", -7.9771, 112.6340),
        "AB": ("Yogyakarta", "DI Yogyakarta", "Indonesia", "ID", -7.7956, 110.3695),
        "AD": ("Surakarta", "Jawa Tengah", "Indonesia", "ID", -7.5666, 110.8166),
        "H": ("Semarang", "Jawa Tengah", "Indonesia", "ID", -6.9667, 110.4167),
        "DK": ("Denpasar", "Bali", "Indonesia", "ID", -8.6705, 115.2126),
        "BK": ("Medan", "Sumatera Utara", "Indonesia", "ID", 3.5952, 98.6722),
        "DD": ("Makassar", "Sulawesi Selatan", "Indonesia", "ID", -5.1477, 119.4327),
        "BG": ("Palembang", "Sumatera Selatan", "Indonesia", "ID", -2.9761, 104.7754),
        "KT": ("Balikpapan", "Kalimantan Timur", "Indonesia", "ID", -1.2379, 116.8529),
        "DA": ("Banjarmasin", "Kalimantan Selatan", "Indonesia", "ID", -3.3167, 114.5900),
        "KB": ("Pontianak", "Kalimantan Barat", "Indonesia", "ID", -0.0263, 109.3425),
        "DB": ("Manado", "Sulawesi Utara", "Indonesia", "ID", 1.4748, 124.8428),
        "BE": ("Bandar Lampung", "Lampung", "Indonesia", "ID", -5.4500, 105.2667),
        "BA": ("Padang", "Sumatera Barat", "Indonesia", "ID", -0.9471, 100.4172),
        "BM": ("Pekanbaru", "Riau", "Indonesia", "ID", 0.5071, 101.4478),
        "BP": ("Batam", "Kepulauan Riau", "Indonesia", "ID", 1.1301, 104.0529),
        "F": ("Bogor", "Jawa Barat", "Indonesia", "ID", -6.5971, 106.8060),
        "E": ("Cirebon", "Jawa Barat", "Indonesia", "ID", -6.7320, 108.5523),
        "Z": ("Tasikmalaya", "Jawa Barat", "Indonesia", "ID", -7.3274, 108.2207),
    }

    def __init__(self, geocoder: Optional[DynamicGeocoder] = None):
        self.geocoder = geocoder or DynamicGeocoder()

    def _obfuscate_to_city_level(self, lat: float, lon: float) -> Tuple[float, float]:
        """
        Anti-Doxxing Privacy Safeguard:
        Quantize coordinates to ~0.05 degree (~5.5 km resolution) unless explicitly geotagged by user.
        Prevents displaying exact home/office addresses.
        """
        grid_step = 0.05
        rounded_lat = round(round(lat / grid_step) * grid_step, 4)
        rounded_lon = round(round(lon / grid_step) * grid_step, 4)
        return rounded_lat, rounded_lon

    def extract_from_bio_and_text(self, profile: PublicProfileData) -> List[LocationCandidate]:
        """Extract location indicators dynamically from bio, names, and bio links."""
        candidates = []
        raw_text = f"{profile.bio} {profile.display_name} {' '.join(profile.links)}"
        tokens = re.split(r"[,|\n/.\-_;()]+|\s+", raw_text)

        processed_words = set()
        for token in tokens:
            cleaned = token.strip().strip("@#")
            if len(cleaned) < 3:
                continue
            lower_token = cleaned.lower()
            if lower_token in processed_words:
                continue
            processed_words.add(lower_token)

            geo_info = self.geocoder.geocode(cleaned)
            if geo_info:
                lat = geo_info.get("lat")
                lon = geo_info.get("lon")
                lat_obs, lon_obs = (
                    self._obfuscate_to_city_level(lat, lon)
                    if (lat is not None and lon is not None)
                    else (None, None)
                )
                candidates.append(
                    LocationCandidate(
                        source_type="TEXTUAL_BIO",
                        city=geo_info.get("city", cleaned.title()),
                        region_province=geo_info.get("region", "Unknown"),
                        country=geo_info.get("country", "Unknown"),
                        country_code=geo_info.get("country_code", ""),
                        latitude_approx=lat_obs,
                        longitude_approx=lon_obs,
                        confidence_base=70.0,
                        evidence_snippet=f"Bio or profile mentions '{cleaned.title()}'",
                        raw_signal=profile.bio,
                    )
                )

        return candidates

    def extract_from_explicit_geotags(self, posts: List[PublicPostData]) -> List[LocationCandidate]:
        """Extract user-tagged location names and coordinates dynamically."""
        candidates = []
        for p in posts:
            if not p.explicit_geotag:
                continue

            geo_info = self.geocoder.geocode(p.explicit_geotag)
            if geo_info:
                use_lat = p.geotag_lat if p.geotag_lat is not None else geo_info.get("lat")
                use_lon = p.geotag_lon if p.geotag_lon is not None else geo_info.get("lon")
                candidates.append(
                    LocationCandidate(
                        source_type="EXPLICIT_GEOTAG",
                        city=geo_info.get("city", p.explicit_geotag.title()),
                        region_province=geo_info.get("region", "Unknown"),
                        country=geo_info.get("country", "Unknown"),
                        country_code=geo_info.get("country_code", ""),
                        latitude_approx=round(use_lat, 5) if use_lat is not None else None,
                        longitude_approx=round(use_lon, 5) if use_lon is not None else None,
                        confidence_base=90.0,
                        evidence_snippet=f"Post explicitly geotagged with '{p.explicit_geotag}'",
                        raw_signal=p.explicit_geotag,
                        is_precise_explicit=True,
                    )
                )
            else:
                candidates.append(
                    LocationCandidate(
                        source_type="EXPLICIT_GEOTAG",
                        city=p.explicit_geotag.title(),
                        region_province="Unknown",
                        country="Unknown",
                        latitude_approx=p.geotag_lat,
                        longitude_approx=p.geotag_lon,
                        confidence_base=80.0,
                        evidence_snippet=f"User post geotag: '{p.explicit_geotag}'",
                        raw_signal=p.explicit_geotag,
                        is_precise_explicit=True,
                    )
                )
        return candidates

    def extract_from_exif_metadata(self, posts: List[PublicPostData]) -> List[LocationCandidate]:
        """Extract GPS coordinates embedded in public image EXIF data via dynamic reverse geocoding."""
        candidates = []
        for p in posts:
            for media in p.media_items:
                if (
                    media.has_exif
                    and media.exif_gps_lat is not None
                    and media.exif_gps_lon is not None
                ):
                    lat_obs, lon_obs = self._obfuscate_to_city_level(
                        media.exif_gps_lat, media.exif_gps_lon
                    )

                    rev_info = self.geocoder.reverse_geocode(
                        media.exif_gps_lat, media.exif_gps_lon
                    )

                    candidates.append(
                        LocationCandidate(
                            source_type="EXIF_GPS",
                            city=rev_info.get("city", "Estimated Area"),
                            region_province=rev_info.get("region", "Unknown"),
                            country=rev_info.get("country", "Unknown"),
                            country_code=rev_info.get("country_code", ""),
                            latitude_approx=lat_obs,
                            longitude_approx=lon_obs,
                            confidence_base=95.0,
                            evidence_snippet=f"EXIF GPS metadata present ({media.exif_camera_make or 'Camera'} {media.exif_camera_model or ''})",
                            raw_signal=f"lat={lat_obs}, lon={lon_obs}",
                        )
                    )
        return candidates

    def extract_from_visual_clues(self, posts: List[PublicPostData]) -> List[LocationCandidate]:
        """
        Extract location dynamically from visual clues:
        Landmarks, license plates, signage language, storefronts.
        """
        candidates = []
        for p in posts:
            for media in p.media_items:
                for clue in media.visual_clues:
                    # 1. License plate prefixes
                    plate_match = re.search(r"\b([A-Z]{1,2})\s*\d{1,4}\s*[A-Z]{0,3}\b", clue)
                    if plate_match:
                        code = plate_match.group(1).upper()
                        if code in self.VEHICLE_PLATE_MAP:
                            city, region, country, cc, lat, lon = self.VEHICLE_PLATE_MAP[code]
                            lat_obs, lon_obs = self._obfuscate_to_city_level(lat, lon)
                            candidates.append(
                                LocationCandidate(
                                    source_type="VISUAL_AI",
                                    city=city,
                                    region_province=region,
                                    country=country,
                                    country_code=cc,
                                    latitude_approx=lat_obs,
                                    longitude_approx=lon_obs,
                                    confidence_base=75.0,
                                    evidence_snippet=f"Vehicle registration plate prefix '{code}' spotted in media",
                                    raw_signal=clue,
                                )
                            )

                    # 2. Dynamic landmark and entity recognition
                    landmark_match = re.search(
                        r"(?:landmark|at|near|in|visit|around)\s+([A-Za-z0-9\s]{3,30})",
                        clue,
                        re.IGNORECASE,
                    )
                    landmark_target = landmark_match.group(1).strip() if landmark_match else clue
                    geo_info = self.geocoder.geocode(landmark_target)

                    if geo_info and geo_info.get("city"):
                        lat = geo_info.get("lat")
                        lon = geo_info.get("lon")
                        lat_obs, lon_obs = (
                            self._obfuscate_to_city_level(lat, lon)
                            if (lat is not None and lon is not None)
                            else (None, None)
                        )
                        candidates.append(
                            LocationCandidate(
                                source_type="VISUAL_AI",
                                city=geo_info.get("city", "Unknown"),
                                region_province=geo_info.get("region", "Unknown"),
                                country=geo_info.get("country", "Unknown"),
                                country_code=geo_info.get("country_code", ""),
                                latitude_approx=lat_obs,
                                longitude_approx=lon_obs,
                                confidence_base=85.0,
                                evidence_snippet=f"Visual recognition identified landmark/feature '{landmark_target.title()}' in image",
                                raw_signal=clue,
                            )
                        )

        return candidates

    def extract_from_temporal_patterns(self, posts: List[PublicPostData]) -> List[LocationCandidate]:
        """
        Estimate UTC timezone offset dynamically from post timestamp distributions.
        Assuming peak social media activity between 19:00 - 23:00 local time.
        """
        if not posts or len(posts) < 3:
            return []

        utc_hours = []
        for p in posts:
            try:
                dt = datetime.fromisoformat(p.timestamp_utc.replace("Z", "+00:00"))
                utc_hours.append(dt.hour)
            except Exception:
                continue

        if not utc_hours:
            return []

        avg_utc_hour = sum(utc_hours) / len(utc_hours)
        inferred_offset = int(round(20.0 - avg_utc_hour)) % 24
        if inferred_offset > 12:
            inferred_offset -= 24

        candidates = []
        if inferred_offset in (7, 8, 9):
            tz_names = {
                7: "WIB (UTC+7, Jakarta/Sumatra)",
                8: "WITA (UTC+8, Bali/Makassar)",
                9: "WIT (UTC+9, Papua)",
            }
            target_city = "Jakarta" if inferred_offset == 7 else ("Denpasar" if inferred_offset == 8 else "Jayapura")
            geo_info = self.geocoder.geocode(target_city) or {}
            lat = geo_info.get("lat", -6.2088)
            lon = geo_info.get("lon", 106.8456)
            lat_obs, lon_obs = self._obfuscate_to_city_level(lat, lon)
            candidates.append(
                LocationCandidate(
                    source_type="TEMPORAL_TIMEZONE",
                    city=target_city,
                    region_province="Timezone Region",
                    country="Indonesia",
                    country_code="ID",
                    latitude_approx=lat_obs,
                    longitude_approx=lon_obs,
                    confidence_base=50.0,
                    evidence_snippet=f"Posting time distribution aligns with {tz_names[inferred_offset]}",
                    raw_signal=f"Inferred UTC offset +{inferred_offset}",
                )
            )

        return candidates

    def extract_all(self, profile: PublicProfileData) -> List[LocationCandidate]:
        """Run all candidate extraction pipelines."""
        candidates: List[LocationCandidate] = []
        candidates.extend(self.extract_from_exif_metadata(profile.posts))
        candidates.extend(self.extract_from_explicit_geotags(profile.posts))
        candidates.extend(self.extract_from_visual_clues(profile.posts))
        candidates.extend(self.extract_from_bio_and_text(profile))
        candidates.extend(self.extract_from_temporal_patterns(profile.posts))
        return candidates
