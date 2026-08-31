"""
Dynamic Geocoding and Reverse-Geocoding Service for GeoTrace OSINT.
Queries open geospatial services (OpenStreetMap Nominatim, Photon by Komoot)
with caching and offline fallback resolver.
"""

import json
import math
import ssl
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


class DynamicGeocoder:
    """
    Dynamic geocoding and reverse geocoding engine with caching and offline fallback.
    """

    def __init__(self, timeout: float = 4.0):
        self.timeout = timeout
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._reverse_cache: Dict[Tuple[float, float], Dict[str, Any]] = {}

        # High-confidence administrative lookup map for fallback
        self._seed_db = {
            "monas": {"city": "Jakarta", "region": "DKI Jakarta", "country": "Indonesia", "country_code": "ID", "lat": -6.1754, "lon": 106.8272},
            "jakarta": {"city": "Jakarta", "region": "DKI Jakarta", "country": "Indonesia", "country_code": "ID", "lat": -6.2088, "lon": 106.8456},
            "surabaya": {"city": "Surabaya", "region": "Jawa Timur", "country": "Indonesia", "country_code": "ID", "lat": -7.2575, "lon": 112.7521},
            "bandung": {"city": "Bandung", "region": "Jawa Barat", "country": "Indonesia", "country_code": "ID", "lat": -6.9175, "lon": 107.6191},
            "malang": {"city": "Malang", "region": "Jawa Timur", "country": "Indonesia", "country_code": "ID", "lat": -7.9771, "lon": 112.6340},
            "yogyakarta": {"city": "Yogyakarta", "region": "DI Yogyakarta", "country": "Indonesia", "country_code": "ID", "lat": -7.7956, "lon": 110.3695},
            "jogja": {"city": "Yogyakarta", "region": "DI Yogyakarta", "country": "Indonesia", "country_code": "ID", "lat": -7.7956, "lon": 110.3695},
            "semarang": {"city": "Semarang", "region": "Jawa Tengah", "country": "Indonesia", "country_code": "ID", "lat": -6.9667, "lon": 110.4167},
            "solo": {"city": "Surakarta", "region": "Jawa Tengah", "country": "Indonesia", "country_code": "ID", "lat": -7.5666, "lon": 110.8166},
            "surakarta": {"city": "Surakarta", "region": "Jawa Tengah", "country": "Indonesia", "country_code": "ID", "lat": -7.5666, "lon": 110.8166},
            "medan": {"city": "Medan", "region": "Sumatera Utara", "country": "Indonesia", "country_code": "ID", "lat": 3.5952, "lon": 98.6722},
            "makassar": {"city": "Makassar", "region": "Sulawesi Selatan", "country": "Indonesia", "country_code": "ID", "lat": -5.1477, "lon": 119.4327},
            "denpasar": {"city": "Denpasar", "region": "Bali", "country": "Indonesia", "country_code": "ID", "lat": -8.6705, "lon": 115.2126},
            "bali": {"city": "Denpasar", "region": "Bali", "country": "Indonesia", "country_code": "ID", "lat": -8.4095, "lon": 115.1889},
            "purworejo": {"city": "Purworejo", "region": "Jawa Tengah", "country": "Indonesia", "country_code": "ID", "lat": -7.7073, "lon": 109.9665},
            "kebumen": {"city": "Kebumen", "region": "Jawa Tengah", "country": "Indonesia", "country_code": "ID", "lat": -7.6698, "lon": 109.6521},
            "bekasi": {"city": "Bekasi", "region": "Jawa Barat", "country": "Indonesia", "country_code": "ID", "lat": -6.2383, "lon": 106.9756},
            "bogor": {"city": "Bogor", "region": "Jawa Barat", "country": "Indonesia", "country_code": "ID", "lat": -6.5971, "lon": 106.8060},
            "depok": {"city": "Depok", "region": "Jawa Barat", "country": "Indonesia", "country_code": "ID", "lat": -6.4025, "lon": 106.7942},
            "tangerang": {"city": "Tangerang", "region": "Banten", "country": "Indonesia", "country_code": "ID", "lat": -6.1783, "lon": 106.6319},
            "tangsel": {"city": "Tangerang Selatan", "region": "Banten", "country": "Indonesia", "country_code": "ID", "lat": -6.2889, "lon": 106.7179},
            "batam": {"city": "Batam", "region": "Kepulauan Riau", "country": "Indonesia", "country_code": "ID", "lat": 1.1301, "lon": 104.0529},
            "singapore": {"city": "Singapore", "region": "Singapore", "country": "Singapore", "country_code": "SG", "lat": 1.3521, "lon": 103.8198},
            "kuala lumpur": {"city": "Kuala Lumpur", "region": "Federal Territory", "country": "Malaysia", "country_code": "MY", "lat": 3.1390, "lon": 101.6869},
            "london": {"city": "London", "region": "Greater London", "country": "United Kingdom", "country_code": "GB", "lat": 51.5074, "lon": -0.1278},
            "tokyo": {"city": "Tokyo", "region": "Kanto", "country": "Japan", "country_code": "JP", "lat": 35.6762, "lon": 139.6503},
        }

    def _get_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def geocode(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a place name, landmark, or address dynamically.
        Returns dict with keys: city, region, country, country_code, lat, lon.
        """
        q_clean = query.strip().lower()
        if not q_clean or len(q_clean) < 2:
            return None

        # Filter out common stop words and generic social words
        stopwords = {
            "the", "and", "from", "with", "official", "account", "profile",
            "page", "channel", "group", "admin", "contact", "support", "help",
            "link", "http", "https", "www", "com", "net", "org", "co", "id"
        }
        if q_clean in stopwords:
            return None

        # 1. Cache hit
        if q_clean in self._cache:
            return self._cache[q_clean]

        # 2. Seed cache direct hit
        if q_clean in self._seed_db:
            res = self._seed_db[q_clean].copy()
            self._cache[q_clean] = res
            return res

        # 3. Dynamic OpenStreetMap Nominatim Live Geocoding
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&addressdetails=1&limit=1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DeltaOSINT-GeoTrace-Engine/3.0 (Security Intelligence Research)"}
            )
            with urllib.request.urlopen(req, context=self._get_ssl_context(), timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    if data and isinstance(data, list) and len(data) > 0:
                        item = data[0]
                        addr = item.get("address", {})
                        city = (
                            addr.get("city")
                            or addr.get("town")
                            or addr.get("municipality")
                            or addr.get("regency")
                            or addr.get("county")
                            or addr.get("state_district")
                            or item.get("name", query.title())
                        )
                        region = addr.get("state") or addr.get("region") or addr.get("province") or "Unknown"
                        country = addr.get("country", "Unknown")
                        country_code = addr.get("country_code", "").upper()
                        lat = float(item["lat"])
                        lon = float(item["lon"])

                        result = {
                            "city": city.title(),
                            "region": region,
                            "country": country,
                            "country_code": country_code,
                            "lat": lat,
                            "lon": lon,
                        }
                        self._cache[q_clean] = result
                        return result
        except Exception:
            pass

        # 4. Fallback search across seed database substring
        for name, data in self._seed_db.items():
            if name == q_clean or (len(name) >= 4 and name in q_clean):
                res = data.copy()
                self._cache[q_clean] = res
                return res

        self._cache[q_clean] = None
        return None

    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates (lat, lon) to human location name dynamically.
        """
        key = (round(lat, 4), round(lon, 4))
        if key in self._reverse_cache:
            return self._reverse_cache[key]

        # 1. Live Nominatim Reverse Geocoding
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DeltaOSINT-GeoTrace-Engine/3.0 (Security Intelligence Research)"}
            )
            with urllib.request.urlopen(req, context=self._get_ssl_context(), timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    if data and isinstance(data, dict):
                        addr = data.get("address", {})
                        city = (
                            addr.get("city")
                            or addr.get("town")
                            or addr.get("municipality")
                            or addr.get("regency")
                            or addr.get("county")
                            or addr.get("state_district")
                            or "Estimated Area"
                        )
                        region = addr.get("state") or addr.get("region") or addr.get("province") or "Unknown"
                        country = addr.get("country", "Unknown")
                        country_code = addr.get("country_code", "").upper()

                        result = {
                            "city": city.title(),
                            "region": region,
                            "country": country,
                            "country_code": country_code,
                        }
                        self._reverse_cache[key] = result
                        return result
        except Exception:
            pass

        # 2. Nearest seed calculation fallback
        closest_city = "Estimated Area"
        closest_reg = "Unknown"
        closest_country = "Unknown"
        closest_cc = ""
        min_dist = float("inf")

        for data in self._seed_db.values():
            dist = math.hypot(lat - data["lat"], lon - data["lon"])
            if dist < min_dist:
                min_dist = dist
                if dist < 1.5:  # Within ~150km
                    closest_city = data["city"]
                    closest_reg = data["region"]
                    closest_country = data["country"]
                    closest_cc = data["country_code"]

        result = {
            "city": closest_city,
            "region": closest_reg,
            "country": closest_country,
            "country_code": closest_cc,
        }
        self._reverse_cache[key] = result
        return result
