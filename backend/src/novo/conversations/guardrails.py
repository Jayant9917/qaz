"""Conversation guardrails for the E2 fast path."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

SENSITIVE_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    (r"sk-[A-Za-z0-9]{16,}", "secret_api_key"),
    (r"(?i)api[_-]?key\s*[:=]\s*\S+", "api_key"),
    (r"(?i)password\s*[:=]\s*\S+", "password"),
    (r"(?i)token\s*[:=]\s*\S+", "token"),
    (r"(?i)bearer\s+[A-Za-z0-9._-]+", "bearer_token"),
)


@dataclass(slots=True)
class GuardrailFinding:
    code: str
    message: str


@dataclass(slots=True)
class GuardrailResult:
    safe_text: str
    findings: list[GuardrailFinding]


_GREETINGS = {"hi", "hii", "hello", "hey", "yo"}


def inspect_text(text: str) -> list[GuardrailFinding]:
    findings: list[GuardrailFinding] = []
    if not text.strip():
        findings.append(GuardrailFinding(code="empty_input", message="Content cannot be empty."))
    for pattern, code in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            findings.append(
                GuardrailFinding(
                    code=code,
                    message="Sensitive material detected and will be redacted from the model path.",
                )
            )
    return findings


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern, _ in SENSITIVE_PATTERNS:
        redacted = re.sub(pattern, "[redacted]", redacted)
    return redacted


def build_stub_reply(content: str, *, fallback_reason: str | None = None) -> GuardrailResult:
    findings = inspect_text(content)
    normalized = content.strip().casefold()
    if fallback_reason:
        reply = f"AI model failed. Fallback used. Reason: {fallback_reason}. Please try again."
    elif normalized in _GREETINGS:
        reply = "Hello. I'm NOVO. I'm here with you."
    elif findings:
        reply = "I can help, but I will not repeat or store sensitive secrets."
    else:
        reply = f"I heard you say: {content.strip()}"
    return GuardrailResult(safe_text=redact_sensitive_text(reply), findings=findings)
