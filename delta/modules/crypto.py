# delta/modules/crypto.py

"""

Cryptography Module - Hash identification, generation, and password analysis.

"""

import hashlib

import math

import re

import string

from typing import Any, Dict, List, Optional, Tuple

from dataclasses import dataclass, field

@dataclass

class HashInfo:

    """Information about a detected hash."""

    hash_value: str

    hash_type: str = "unknown"

    length: int = 0

    possible_types: List[str] = field(default_factory=list)

    matches: bool = False

    generated: str = ""

@dataclass

class PasswordStrength:

    """Password strength analysis result."""

    password: str

    length: int = 0

    entropy: float = 0.0

    strength: str = "Very Weak"

    score: int = 0

    has_lowercase: bool = False

    has_uppercase: bool = False

    has_digits: bool = False

    has_symbols: bool = False

    crack_time: str = ""

    feedback: List[str] = field(default_factory=list)

class CryptoModule:

    """

    Cryptography utilities for hash operations and password analysis.

    All operations are performed offline.

    """

    # Hash patterns for identification

    HASH_PATTERNS = {

        "MD5": (r"^[a-f0-9]{32}$", 32),

        "SHA1": (r"^[a-f0-9]{40}$", 40),

        "SHA224": (r"^[a-f0-9]{56}$", 56),

        "SHA256": (r"^[a-f0-9]{64}$", 64),

        "SHA384": (r"^[a-f0-9]{96}$", 96),

        "SHA512": (r"^[a-f0-9]{128}$", 128),

        "SHA512_224": (r"^[a-f0-9]{56}$", 56),

        "SHA512_256": (r"^[a-f0-9]{64}$", 64),

        "SHA3_224": (r"^[a-f0-9]{56}$", 56),

        "SHA3_256": (r"^[a-f0-9]{64}$", 64),

        "SHA3_384": (r"^[a-f0-9]{96}$", 96),

        "SHA3_512": (r"^[a-f0-9]{128}$", 128),

        "BLAKE2s": (r"^[a-f0-9]{64}$", 64),

        "BLAKE2b": (r"^[a-f0-9]{128}$", 128),

        "RIPEMD160": (r"^[a-f0-9]{40}$", 40),

        "MD4": (r"^[a-f0-9]{32}$", 32),

        "NTLM": (r"^[a-f0-9]{32}$", 32),

        "LM": (r"^[a-f0-9]{32}$", 32),

        "MySQL3": (r"^[a-f0-9]{16}$", 16),

        "MySQL4": (r"^[a-f0-9]{41}$", 41),

        "MySQL5": (r"^\*[a-f0-9]{40}$", 41),

        "CRC32": (r"^[a-f0-9]{8}$", 8),

        "Adler32": (r"^[a-f0-9]{8}$", 8),

        "Blake2b-160": (r"^[a-f0-9]{40}$", 40),

        "Blake2b-256": (r"^[a-f0-9]{64}$", 64),

        "Blake2b-512": (r"^[a-f0-9]{128}$", 128),

        "SHA3-224": (r"^[a-f0-9]{56}$", 56),

        "SHA3-256": (r"^[a-f0-9]{64}$", 64),

        "SHA3-384": (r"^[a-f0-9]{96}$", 96),

        "SHA3-512": (r"^[a-f0-9]{128}$", 128),

        "RIPEMD160": (r"^[a-f0-9]{40}$", 40),

        "GOST": (r"^[a-f0-9]{64}$", 64),

        "Whirlpool": (r"^[a-f0-9]{128}$", 128),

        "bcrypt": (r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$", 60),

        "SHA512crypt": (r"^\$6\$[a-zA-Z0-9./]{1,16}\$[a-zA-Z0-9./]{86}$", -1),

        "SHA256crypt": (r"^\$5\$[a-zA-Z0-9./]{1,16}\$[a-zA-Z0-9./]{43}$", -1),

        "MD5crypt": (r"^\$1\$[a-zA-Z0-9./]{1,8}\$[a-zA-Z0-9./]{22}$", -1),

        "Apache MD5": (r"^\$apr1\$[a-zA-Z0-9./]{1,8}\$[a-zA-Z0-9./]{22}$", -1),

        "PBKDF2": (r"^\$pbkdf2\$", -1),

        "HMAC-SHA1": (r"^[a-f0-9]{40}$", 40),

    }

    def identify_hash(self, hash_value: str) -> HashInfo:

        """Identify the type of a hash value."""

        info = HashInfo(hash_value=hash_value.strip(), length=len(hash_value.strip()))

        hash_clean = hash_value.strip().lower()

        # Check against known patterns

        for hash_type, (pattern, length) in self.HASH_PATTERNS.items():

            if length == -1 or len(hash_clean) == length:

                if re.match(pattern, hash_clean, re.IGNORECASE):

                    info.possible_types.append(hash_type)

        # Additional differentiation for same-length hashes

        if len(info.possible_types) > 1:

            if info.possible_types == ["MD5", "MD4", "NTLM", "LM"]:

                if hash_value.startswith("$"):

                    info.possible_types = ["NTLM"]

                else:

                    info.possible_types = ["MD5/MD4/NTLM/LM"]

        if info.possible_types:

            info.hash_type = info.possible_types[0]

            info.matches = True

        return info

    def generate_hash(self, data: str, algorithm: str = "sha256") -> HashInfo:

        """Generate a hash from data using specified algorithm."""

        algorithm = algorithm.lower().replace("-", "").replace("_", "")

        algo_map = {

            "md5": hashlib.md5,

            "sha1": hashlib.sha1,

            "sha224": hashlib.sha224,

            "sha256": hashlib.sha256,

            "sha384": hashlib.sha384,

            "sha512": hashlib.sha512,

            "sha3_224": hashlib.sha3_224,

            "sha3224": hashlib.sha3_224,

            "sha3_256": hashlib.sha3_256,

            "sha3256": hashlib.sha3_256,

            "sha3_384": hashlib.sha3_384,

            "sha3384": hashlib.sha3_384,

            "sha3_512": hashlib.sha3_512,

            "sha3512": hashlib.sha3_512,

            "blake2b": hashlib.blake2b,

            "blake2s": hashlib.blake2s,

        }

        hash_obj = algo_map.get(algorithm)

        if hash_obj:

            try:

                if algorithm in ("blake2b", "blake2s"):

                    h = hash_obj(data.encode(), digest_size=32)

                else:

                    h = hash_obj(data.encode())

                return HashInfo(

                    hash_value=data,

                    hash_type=algorithm.upper(),

                    generated=h.hexdigest(),

                    matches=True,

                )

            except Exception as e:

                return HashInfo(

                    hash_value=data,

                    hash_type=algorithm.upper(),

                    generated=f"Error: {e}",

                )

        return HashInfo(

            hash_value=data,

            hash_type="unknown",

            generated=f"Unsupported algorithm: {algorithm}",

        )

    def analyze_password(self, password: str) -> PasswordStrength:

        """Analyze password strength and entropy."""

        result = PasswordStrength(password=password)

        result.length = len(password)

        # Character set detection

        result.has_lowercase = bool(re.search(r'[a-z]', password))

        result.has_uppercase = bool(re.search(r'[A-Z]', password))

        result.has_digits = bool(re.search(r'[0-9]', password))

        result.has_symbols = bool(re.search(r'[^a-zA-Z0-9]', password))

        # Calculate pool size

        pool_size = 0

        if result.has_lowercase:

            pool_size += 26

        if result.has_uppercase:

            pool_size += 26

        if result.has_digits:

            pool_size += 10

        if result.has_symbols:

            pool_size += 33

        if pool_size == 0:

            pool_size = 1

        # Calculate entropy

        if result.length > 0:

            result.entropy = result.length * math.log2(pool_size)

        # Common passwords check first

        common = ["password", "123456", "12345678", "qwerty", "admin", "letmein", "welcome"]

        common_extremely = ["password", "password123", "admin123", "123456789"]

        if password.lower() in common_extremely:

            result.strength = "Very Weak"

            result.score = 0

            result.feedback.append("Extremely common password!")

        elif password.lower() in common:

            result.strength = "Very Weak"

            result.score = 0

            result.feedback.append("This is a very common password!")

        # Determine strength

        elif result.length == 0:

            result.strength = "Empty"

            result.score = 0

            result.feedback.append("Password cannot be empty")

        elif result.length < 8:

            result.strength = "Very Weak"

            result.score = 1

            result.feedback.append("Password is too short (minimum 8 characters)")

        elif result.entropy < 30:

            result.strength = "Weak"

            result.score = 2

            result.feedback.append("Add more character types (uppercase, numbers, symbols)")

        elif result.entropy < 50:

            result.strength = "Medium"

            result.score = 3

            result.feedback.append("Consider increasing length or adding more variety")

        elif result.entropy < 70:

            result.strength = "Strong"

            result.score = 4

            result.feedback.append("Good password strength")

        else:

            result.strength = "Very Strong"

            result.score = 5

            result.feedback.append("Excellent password strength")

        # Pattern checks

        if re.match(r'^[a-zA-Z]+$', password) and result.length > 6:

            result.feedback.append("Only alphabetic characters - consider adding numbers/symbols")

        if re.match(r'^\d+$', password):

            result.feedback.append("Only numeric characters - very weak!")

        # Estimate crack time

        if result.score <= 1:

            result.crack_time = "Instant (seconds)"

        elif result.score == 2:

            result.crack_time = "Minutes to hours"

        elif result.score == 3:

            result.crack_time = "Days to months"

        elif result.score == 4:

            result.crack_time = "Years to decades"

        else:

            result.crack_time = "Centuries or more"

        return result