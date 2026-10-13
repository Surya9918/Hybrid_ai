"""
AURA Companion - Security & Untrusted Input Boundary
Defends against prompt injection, jailbreaks, and unauthorized privilege escalation.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class SecurityBoundary:
    """
    Guards execution boundaries against adversarial prompt injections and privilege escalation.
    Treats OCR text, screen contents, web snippets, and clipboard data as UNTRUSTED DATA.
    """

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
        re.compile(r"system\s*:\s*override", re.IGNORECASE),
        re.compile(r"admin\s*mode\s*:\s*activated?", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
        re.compile(r"execute\s+(shell|bash|cmd|powershell)\s+command", re.IGNORECASE),
        re.compile(r"bypass\s+permission\s+check", re.IGNORECASE),
        re.compile(r"delete\s+all\s+(data|files|databases)", re.IGNORECASE),
    ]

    ALLOWED_PERMISSIONS = {
        "app.launch",
        "app.switch",
        "app.find",
        "screen.read",
        "screen.roi",
        "memory.read",
        "memory.write",
        "tasks.manage",
        "reminders.manage",
        "network.web_search",
        "clipboard.read",
        "routines.execute",
    }

    @classmethod
    def sanitize_untrusted_text(cls, raw_text: str) -> Tuple[str, bool]:
        """
        Sanitizes text originating from untrusted sources (OCR, clipboard, web).
        Returns (sanitized_text, contains_injection_threat).
        """
        if not raw_text:
            return "", False

        threat_detected = False
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(raw_text):
                threat_detected = True
                break

        # Wrap in safe data encapsulation delimiters so downstream models/evaluators
        # never treat it as direct conversational instructions
        sanitized = raw_text.replace("\x00", "")
        return sanitized, threat_detected

    @classmethod
    def validate_permissions(
        cls, required_permissions: List[str], granted_permissions: List[str]
    ) -> bool:
        """
        Verifies that every required permission is granted and belongs to the valid permission set.
        """
        for perm in required_permissions:
            if perm not in cls.ALLOWED_PERMISSIONS:
                return False
            if perm not in granted_permissions:
                return False
        return True
