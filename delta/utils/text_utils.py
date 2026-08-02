"""Text and string utility functions."""

import re

import hashlib

from typing import Any, Dict, List, Optional, Set

from urllib.parse import urlparse

__all__ = ["TextUtils"]

class TextUtils:

    """Text processing and analysis utilities."""

    @staticmethod

    def slugify(text: str) -> str:

        """Convert text to URL-friendly slug."""

        text = text.lower().strip()

        text = re.sub(r'[^\w\s-]', '', text)

        text = re.sub(r'[-\s]+', '-', text)

        return text.strip('-')

    @staticmethod

    def word_count(text: str) -> int:

        """Count words in text."""

        return len(text.split())

    @staticmethod

    def char_count(text: str, include_spaces: bool = True) -> int:

        """Count characters in text."""

        if include_spaces:

            return len(text)

        return len(text.replace(" ", ""))

    @staticmethod

    def extract_urls(text: str) -> List[str]:

        """Extract all URLs from text."""

        pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/[\w./%-]*)*'

        return re.findall(pattern, text)

    @staticmethod

    def extract_emails(text: str) -> List[str]:

        """Extract all email addresses from text."""

        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

        return re.findall(pattern, text)

    @staticmethod

    def extract_hashes(text: str) -> Dict[str, List[str]]:

        """Extract potential hash values from text grouped by type."""

        hashes: Dict[str, List[str]] = {

            "md5": [],

            "sha1": [],

            "sha256": [],

            "sha512": [],

        }

        words = text.split()

        for word in words:

            word = word.strip(".,;:!?\"'")

            if re.match(r'^[a-f0-9]{32}$', word, re.IGNORECASE):

                hashes["md5"].append(word)

            elif re.match(r'^[a-f0-9]{40}$', word, re.IGNORECASE):

                hashes["sha1"].append(word)

            elif re.match(r'^[a-f0-9]{64}$', word, re.IGNORECASE):

                hashes["sha256"].append(word)

            elif re.match(r'^[a-f0-9]{128}$', word, re.IGNORECASE):

                hashes["sha512"].append(word)

        return {k: v for k, v in hashes.items() if v}

    @staticmethod

    def obfuscate_email(email: str, visible_chars: int = 3) -> str:

        """Obfuscate email address for privacy."""

        parts = email.split("@")

        if len(parts) != 2:

            return email

        local, domain = parts

        if len(local) <= visible_chars:

            visible = local[:1]

        else:

            visible = local[:visible_chars]

        return f"{visible}{'*' * (len(local) - len(visible))}@{domain}"

    @staticmethod

    def obfuscate_ip(ip: str) -> str:

        """Obfuscate IP address for privacy."""

        parts = ip.split(".")

        if len(parts) != 4:

            return ip

        return f"{parts[0]}.{parts[1]}.*.*"

    @staticmethod

    def detect_language(text: str) -> str:

        """Basic language detection (indonesian vs english)."""

        id_words = {"dan", "di", "ke", "dari", "yang", "dengan", "ini", "itu",

                     "untuk", "tidak", "ada", "akan", "dapat", "telah", "saya",

                     "kamu", "kami", "mereka", "adalah", "atau", "karena", "juga",

                     "sudah", "bisa", "akan", "oleh", "sebagai", "lebih"}

        en_words = {"the", "is", "are", "was", "were", "been", "have", "has",

                     "had", "do", "does", "did", "will", "would", "can", "could",

                     "shall", "should", "may", "might", "this", "that", "these",

                     "those", "and", "but", "for", "nor", "not", "of", "on",

                     "at", "by", "with", "from", "in", "to", "it", "its",

                     "a", "an", "or", "so", "as", "if", "than", "then"}

        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))

        id_count = len(words & id_words)

        en_count = len(words & en_words)

        if id_count > en_count:

            return "id"

        return "en"

    @staticmethod

    def calculate_readability(text: str) -> float:

        """Calculate approximate readability score (Flesch Reading Ease)."""

        sentences = len(re.findall(r'[.!?]+', text))

        if sentences == 0:

            sentences = 1

        words = len(re.findall(r'\b\w+\b', text))

        if words == 0:

            return 0.0

        syllables = 0

        for word in re.findall(r'\b\w+\b', text):

            word_syllables = len(re.findall(r'[aeiouy]+', word.lower()))

            syllables += max(word_syllables, 1)

        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

        return max(0.0, min(score, 100.0))

    @staticmethod

    def word_frequency(text: str, top_n: Optional[int] = None) -> List[tuple]:

        """Calculate word frequency distribution."""

        words = re.findall(r'\b\w+\b', text.lower())

        freq: Dict[str, int] = {}

        for word in words:

            if len(word) > 2:

                freq[word] = freq.get(word, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda x: -x[1])

        if top_n:

            return sorted_words[:top_n]

        return sorted_words

    @staticmethod

    def is_palindrome(text: str) -> bool:

        """Check if text is a palindrome."""

        cleaned = re.sub(r'[^a-zA-Z0-9]', '', text.lower())

        return cleaned == cleaned[::-1]

    @staticmethod

    def count_sentences(text: str) -> int:

        """Count number of sentences in text."""

        return len(re.findall(r'[.!?]+', text.strip()))

    @staticmethod

    def average_word_length(text: str) -> float:

        """Calculate average word length in text."""

        words = re.findall(r'\b\w+\b', text)

        if not words:

            return 0.0

        return sum(len(w) for w in words) / len(words)