# delta/modules/encode.py
"""
Encoding/Decoding Module - Base64, Hex, URL, JWT encoding and decoding.
"""

import base64
import json
import urllib.parse
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class EncodeResult:
    """Encoding/decoding operation result."""
    input_text: str
    operation: str
    result: str = ""
    error: str = ""
    success: bool = False
    format: str = ""


class EncodeModule:
    """
    Encoding and decoding utilities for various formats.
    Supports Base64, Hex, URL, and JWT operations.
    """

    def decode_base64(self, data: str) -> EncodeResult:
        """Decode Base64 encoded data."""
        result = EncodeResult(input_text=data, operation="decode", format="base64")
        try:
            # Add padding if needed
            padding = 4 - len(data) % 4
            if padding != 4:
                data_padded = data + "=" * padding
            else:
                data_padded = data
            
            decoded = base64.b64decode(data_padded)
            result.result = decoded.decode("utf-8", errors="replace")
            result.success = True
        except Exception as e:
            result.error = f"Base64 decode error: {e}"
        return result

    def encode_base64(self, data: str) -> EncodeResult:
        """Encode data to Base64."""
        result = EncodeResult(input_text=data, operation="encode", format="base64")
        try:
            encoded = base64.b64encode(data.encode()).decode()
            result.result = encoded
            result.success = True
        except Exception as e:
            result.error = f"Base64 encode error: {e}"
        return result

    def decode_hex(self, data: str) -> EncodeResult:
        """Decode hexadecimal string."""
        result = EncodeResult(input_text=data, operation="decode", format="hex")
        try:
            data_clean = data.replace(" ", "").replace("0x", "").replace("\\x", "")
            decoded = bytes.fromhex(data_clean)
            result.result = decoded.decode("utf-8", errors="replace")
            result.success = True
        except Exception as e:
            result.error = f"Hex decode error: {e}"
        return result

    def encode_hex(self, data: str) -> EncodeResult:
        """Encode data to hexadecimal."""
        result = EncodeResult(input_text=data, operation="encode", format="hex")
        try:
            encoded = data.encode().hex()
            result.result = encoded
            result.success = True
        except Exception as e:
            result.error = f"Hex encode error: {e}"
        return result

    def decode_url(self, data: str) -> EncodeResult:
        """Decode URL-encoded string."""
        result = EncodeResult(input_text=data, operation="decode", format="url")
        try:
            decoded = urllib.parse.unquote(data)
            result.result = decoded
            result.success = True
        except Exception as e:
            result.error = f"URL decode error: {e}"
        return result

    def encode_url(self, data: str) -> EncodeResult:
        """Encode data to URL-encoded string."""
        result = EncodeResult(input_text=data, operation="encode", format="url")
        try:
            encoded = urllib.parse.quote(data, safe="")
            result.result = encoded
            result.success = True
        except Exception as e:
            result.error = f"URL encode error: {e}"
        return result

    def decode_jwt(self, token: str) -> EncodeResult:
        """Decode JWT token without verification."""
        result = EncodeResult(input_text=token[:50] + "...", operation="decode", format="jwt")
        try:
            parts = token.split(".")
            if len(parts) != 3:
                result.error = "Invalid JWT format: expected 3 parts"
                return result

            decoded_parts = []
            for i, part in enumerate(parts[:2]):  # Only decode header and payload
                # Add padding
                padding = 4 - len(part) % 4
                if padding != 4:
                    part_padded = part + "=" * padding
                else:
                    part_padded = part
                
                decoded = base64.urlsafe_b64decode(part_padded)
                try:
                    parsed = json.loads(decoded)
                    formatted = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    formatted = decoded.decode("utf-8", errors="replace")
                
                decoded_parts.append(formatted)

            result.result = f"HEADER:\n{decoded_parts[0]}\n\nPAYLOAD:\n{decoded_parts[1]}"
            result.success = True
        except Exception as e:
            result.error = f"JWT decode error: {e}"
        return result

    def format_json(self, data: str) -> EncodeResult:
        """Format and validate JSON string."""
        result = EncodeResult(input_text=data[:50], operation="format", format="json")
        try:
            parsed = json.loads(data)
            formatted = json.dumps(parsed, indent=2, sort_keys=False)
            result.result = formatted
            result.success = True
        except json.JSONDecodeError as e:
            result.error = f"JSON parse error: {e}"
        except Exception as e:
            result.error = f"Error: {e}"
        return result