"""

GeoIP Module - IP geolocation lookup using public APIs.

Provides IP address location, ISP, and other geographic information.

"""

import json

import socket

from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional

from urllib.request import urlopen, Request

from urllib.error import URLError

__all__ = ["GeoIPModule", "GeoIPResult"]

@dataclass

class GeoIPResult:

    """IP geolocation lookup result."""

    ip: str

    country: str = ""

    country_code: str = ""

    region: str = ""

    city: str = ""

    zip_code: str = ""

    lat: float = 0.0

    lon: float = 0.0

    timezone: str = ""

    isp: str = ""

    org: str = ""

    as_number: str = ""

    success: bool = False

    error: str = ""

class GeoIPModule:

    """

    IP geolocation module.

    Looks up geographic information for IP addresses using ip-api.com.

    """

    API_URL = "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,city,zip,lat,lon,timezone,isp,org,as,query"

    REQUEST_TIMEOUT = 10

    def _validate_ip(self, ip: str) -> bool:

        """Validate IP address format."""

        try:

            socket.inet_aton(ip)

            return True

        except socket.error:

            return False

    def lookup(self, ip: str) -> GeoIPResult:

        """Look up geolocation for an IP address."""

        result = GeoIPResult(ip=ip)

        if not self._validate_ip(ip):

            result.error = f"Invalid IP address: {ip}"

            return result

        try:

            url = self.API_URL.format(ip=ip)

            req = Request(url, headers={"User-Agent": "Delta-CLI/1.0"})

            with urlopen(req, timeout=self.REQUEST_TIMEOUT) as response:

                data = json.loads(response.read().decode())

            if data.get("status") == "success":

                result.country = data.get("country", "")

                result.country_code = data.get("countryCode", "")

                result.region = data.get("region", "")

                result.city = data.get("city", "")

                result.zip_code = data.get("zip", "")

                result.lat = data.get("lat", 0.0)

                result.lon = data.get("lon", 0.0)

                result.timezone = data.get("timezone", "")

                result.isp = data.get("isp", "")

                result.org = data.get("org", "")

                result.as_number = data.get("as", "")

                result.success = True

            else:

                result.error = data.get("message", "Unknown error")

        except URLError as e:

            result.error = f"API request failed: {e.reason}"

        except Exception as e:

            result.error = f"Lookup error: {e}"

        return result

    def lookup_local(self) -> GeoIPResult:

        """Look up geolocation for the local machine."""

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            s.connect(("8.8.8.8", 80))

            local_ip = s.getsockname()[0]

            s.close()

            return self.lookup(local_ip)

        except Exception as e:

            return GeoIPResult(ip="", error=f"Could not determine local IP: {e}")