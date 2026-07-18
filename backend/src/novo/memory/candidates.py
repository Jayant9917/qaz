"""Deterministic, conservative memory-candidate detection for chat input."""

from __future__ import annotations

import re
from dataclasses import dataclass

_DURABLE_PATTERNS = (
    re.compile(r"\bI\s+(?:prefer|like|love|hate|dislike|use|work|live|study)\b", re.I),
    re.compile(
        r"\bmy\s+(?:name|project|job|role|team|timezone|language|goal|birthday|home|company)\b",
        re.I,
    ),
    re.compile(r"\bcall me\b", re.I),
    re.compile(r"\b(?:remember that|remember this|please remember|don't forget)\b", re.I),
)
_HIGH_CONFIDENCE_PATTERNS = (
    re.compile(r"\b(?:remember that|remember this|please remember|don't forget)\b", re.I),
    re.compile(r"\b(?:my name is|my project is|call me)\b", re.I),
    re.compile(r"\bI\s+(?:prefer|use|work on|live in)\b", re.I),
)
_SECRET_PATTERN = re.compile(
    r"\b(?:password|passcode|api[ _-]?key|secret|token|recovery code|private key|seed phrase)\b",
    re.I,
)
_QUESTION_PATTERN = re.compile(r"\?\s*$")


@dataclass(frozen=True)
class MemoryCandidate:
    title: str
    content: str
    kind: str = "long_term"
    classification: str = "private"
    confidence: float = 0.78
    importance: float = 0.65
    auto_save: bool = False
    reason: str = "This looks like a durable preference or personal fact."


def _title_for(content: str) -> str:
    compact = " ".join(content.split()).strip().rstrip(".!?")
    if compact.lower().startswith(("i prefer", "i like", "i love", "i hate", "i dislike")):
        return "Communication or personal preference"
    if compact.lower().startswith("my "):
        return compact[:80]
    return "Personal context"



def contains_secret(content: str) -> bool:
    """Return whether content looks like a credential or recovery secret."""
    return bool(_SECRET_PATTERN.search(content))
def detect_memory_candidate(content: str) -> MemoryCandidate | None:
    """Return a candidate for owner approval; this detector never saves automatically."""

    normalized = " ".join(content.split()).strip()
    if len(normalized) < 12 or len(normalized) > 1000:
        return None
    if _SECRET_PATTERN.search(normalized) or _QUESTION_PATTERN.search(normalized):
        return None
    if not any(pattern.search(normalized) for pattern in _DURABLE_PATTERNS):
        return None
    return MemoryCandidate(title=_title_for(normalized), content=normalized)
