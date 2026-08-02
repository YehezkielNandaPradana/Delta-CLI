# delta/modules/ssl.py

"""

SSL/TLS Analysis Module - Checks certificate validity, protocols, and security.

"""

import socket

import ssl

import time

from datetime import datetime

from typing import Any, Dict, List, Optional, Tuple

from dataclasses import dataclass, field

@dataclass

class SSLCertificateInfo:

    """SSL/TLS certificate information."""

    host: str

    port: int = 443

    subject: Dict = field(default_factory=dict)

    issuer: Dict = field(default_factory=dict)

    version: str = ""

    not_before: str = ""

    not_after: str = ""

    serial_number: str = ""

    algorithm: str = ""

    protocol: str = ""

    expired: bool = False

    days_remaining: int = 0

    self_signed: bool = False

    valid: bool = False

    errors: List[str] = field(default_factory=list)

class SSLModule:

    """

    SSL/TLS certificate analysis and security checking.

    Uses Python's ssl standard library.

    """

    def __init__(self):

        self.context = self._create_context()

        self._timeout = 5

    def _create_context(self) -> ssl.SSLContext:

        """Create SSL context for checking."""

        context = ssl.create_default_context()

        context.check_hostname = False

        context.verify_mode = ssl.CERT_NONE

        return context

    def check(self, host: str, port: int = 443, timeout: int = 5) -> SSLCertificateInfo:

        """Check SSL/TLS certificate for a host."""

        info = SSLCertificateInfo(host=host, port=port)

        try:

            with socket.create_connection((host, port), timeout=timeout) as sock:

                with self.context.wrap_socket(sock, server_hostname=host) as ssock:

                    cert = ssock.getpeercert()

                    info.protocol = ssock.version() or "unknown"

                    if cert:

                        # Subject

                        subject = cert.get("subject", [])

                        info.subject = {k: v for item in subject for k, v in item}

                        # Issuer

                        issuer = cert.get("issuer", [])

                        info.issuer = {k: v for item in issuer for k, v in item}

                        # Dates

                        info.not_before = cert.get("notBefore", "")

                        info.not_after = cert.get("notAfter", "")

                        # Check expiration

                        if info.not_after:

                            try:

                                expiry = datetime.strptime(

                                    info.not_after, "%b %d %H:%M:%S %Y %Z"

                                )

                                now = datetime.now()

                                info.expired = expiry < now

                                info.days_remaining = (expiry - now).days

                            except ValueError:

                                pass

                        info.version = str(cert.get("version", ""))

                        info.serial_number = str(cert.get("serialNumber", ""))

                        info.algorithm = cert.get("signatureAlgorithm", "")

                        # Check self-signed

                        if info.subject.get("CN", "") == info.issuer.get("CN", ""):

                            info.self_signed = True

                        info.valid = True

        except ssl.SSLError as e:

            info.errors.append(f"SSL Error: {e}")

        except socket.timeout:

            info.errors.append("Connection timed out")

        except ConnectionRefusedError:

            info.errors.append("Connection refused")

        except Exception as e:

            info.errors.append(f"Error: {e}")

        return info

    def check_all_protocols(self, host: str, port: int = 443) -> Dict[str, bool]:

        """Check which TLS protocols are supported."""

        protocols = {

            "SSLv2": ssl.PROTOCOL_SSLv23,  # Will fail if not supported

            "SSLv3": ssl.PROTOCOL_SSLv3 if hasattr(ssl, 'PROTOCOL_SSLv3') else None,

            "TLSv1.0": ssl.PROTOCOL_TLSv1 if hasattr(ssl, 'PROTOCOL_TLSv1') else None,

            "TLSv1.1": ssl.PROTOCOL_TLSv1_1 if hasattr(ssl, 'PROTOCOL_TLSv1_1') else None,

            "TLSv1.2": ssl.PROTOCOL_TLSv1_2 if hasattr(ssl, 'PROTOCOL_TLSv1_2') else None,

        }

        results = {}

        for proto_name, proto_const in protocols.items():

            if proto_const is None:

                results[proto_name] = False

                continue

            try:

                ctx = ssl.SSLContext(proto_const)

                ctx.check_hostname = False

                ctx.verify_mode = ssl.CERT_NONE

                with socket.create_connection((host, port), timeout=3) as sock:

                    with ctx.wrap_socket(sock, server_hostname=host) as ssock:

                        results[proto_name] = True

            except Exception:

                results[proto_name] = False

        return results