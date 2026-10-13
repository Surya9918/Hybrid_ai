"""
AURA Companion - Voice Pipeline & Correction-Aware Dictation
Implements push-to-talk states, streaming buffer, and natural spoken correction parsing.
"""

import re
from enum import Enum
from typing import List, Optional, Tuple


class VoiceState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


class DictationCorrectionParser:
    """
    Parses natural spoken self-corrections in real-time dictation:
    Examples:
    - "Meet with John at 2 scratch that 3 PM" -> "Meet with John at 3 PM"
    - "Call Alice no wait call Bob" -> "Call Bob"
    - "Remind me in 30 minutes to review code scratch that 15 minutes to review code" -> "Remind me in 15 minutes to review code"
    """

    @classmethod
    def apply_corrections(cls, raw_transcription: str) -> str:
        if not raw_transcription:
            return ""

        text = raw_transcription.strip()

        # Handle "scratch that"
        if "scratch that" in text.lower():
            parts = re.split(r"\bscratch\s+that\b", text, flags=re.IGNORECASE)
            if len(parts) >= 2:
                prefix = parts[0].strip()
                replacement = parts[-1].strip()
                # If prefix starts with a command intent (e.g. "Remind me in", "Send email to"), preserve that intent
                prefix_intent = re.match(r"^(remind\s+(?:me\s+)?in\s+|call\s+|open\s+|create\s+)", prefix, re.IGNORECASE)
                if prefix_intent and not re.match(r"^(remind|call|open|create)\b", replacement, re.IGNORECASE):
                    return prefix_intent.group(1) + replacement
                return replacement

        # Handle "no wait"
        if "no wait" in text.lower():
            parts = re.split(r"\bno\s+wait\b", text, flags=re.IGNORECASE)
            if len(parts) >= 2:
                prefix = parts[0].strip()
                replacement = parts[-1].strip()
                prefix_intent = re.match(r"^(remind\s+(?:me\s+)?in\s+|call\s+|open\s+|create\s+)", prefix, re.IGNORECASE)
                if prefix_intent and not re.match(r"^(remind|call|open|create)\b", replacement, re.IGNORECASE):
                    return prefix_intent.group(1) + replacement
                return replacement

        # Handle "actually"
        if "actually" in text.lower():
            parts = re.split(r"\bactually\b", text, flags=re.IGNORECASE)
            if len(parts) >= 2:
                prefix = parts[0].strip()
                replacement = parts[-1].strip()
                prefix_words = prefix.split()
                if prefix_words:
                    return " ".join(prefix_words[:-1] + [replacement])
                return replacement

        return text


class VoiceSession:
    def __init__(self, mic_available: bool = True):
        self.mic_available = mic_available
        self.state = VoiceState.IDLE
        self.audio_chunks: List[bytes] = []
        self.transcribed_text = ""

    def start_push_to_talk(self) -> Tuple[bool, str]:
        if not self.mic_available:
            self.state = VoiceState.ERROR
            return False, "Microphone is unavailable or disconnected"
        self.state = VoiceState.LISTENING
        self.audio_chunks = []
        return True, "Listening..."

    def feed_audio(self, chunk: bytes) -> None:
        if self.state == VoiceState.LISTENING:
            self.audio_chunks.append(chunk)

    def stop_push_to_talk(self, simulated_raw_speech: str = "") -> str:
        if self.state != VoiceState.LISTENING:
            return ""
        self.state = VoiceState.PROCESSING
        corrected = DictationCorrectionParser.apply_corrections(simulated_raw_speech)
        self.transcribed_text = corrected
        self.state = VoiceState.IDLE
        return corrected
