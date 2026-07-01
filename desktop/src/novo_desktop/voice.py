"""Shared NOVO voice profile and pipeline metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VoiceProfile:
    engine: str
    model: str
    locale: str
    description: str
    length_scale: float = 0.82


NOVO_VOICE_PROFILE = VoiceProfile(
    engine="Piper",
    model="en_US-amy-medium",
    locale="en_US",
    description="NOVO female English voice",
    length_scale=0.82,
)

NOVO_VOICE_PIPELINE = (
    "Microphone",
    "VAD",
    "faster-whisper",
    "NOVO backend chat API",
    "Streaming response",
    "Piper",
    "Speaker",
)


def voice_summary() -> str:
    return f"{NOVO_VOICE_PROFILE.engine} / {NOVO_VOICE_PROFILE.model}"


def pipeline_summary() -> str:
    return " -> ".join(NOVO_VOICE_PIPELINE)
