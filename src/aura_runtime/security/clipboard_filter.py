"""
AURA Companion - Clipboard Privacy & Sensitive Content Filter
Detects passwords, API keys, private keys, and payment credentials to prevent leakage.
"""

import re
from typing import Tuple


class ClipboardPrivacyFilter:
    PATTERNS = [
        # Private Keys
        re.compile(r"-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA|PGP)?\s*PRIVATE\s+KEY-----", re.IGNORECASE),
        # JWT / Bearer tokens
        re.compile(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
        # API Keys (e.g. OpenAI, AWS, GitHub)
        re.compile(r"(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{30,}|AKIA[0-9A-Z]{16})"),
        # Credit Card numbers (Luhn candidate 13-19 digits)
        re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
        # Explicit password fields or key/value pairs
        re.compile(r"(?:password|passwd|secret|api_key)\s*[:=]\s*['\"]?[^\s'\"]+", re.IGNORECASE),
    ]

    @classmethod
    def is_sensitive(cls, text: str) -> Tuple[bool, str]:
        if not text:
            return False, ""
        for pattern in cls.PATTERNS:
            if pattern.search(text):
                return True, "Contains sensitive credentials (API key, private key, token, or password)"
        return False, ""

    @classmethod
    def filter_text_for_history(cls, text: str) -> str:
        sensitive, _ = cls.is_sensitive(text)
        if sensitive:
            return "[REDACTED: Sensitive content excluded from clipboard history]"
        return text
