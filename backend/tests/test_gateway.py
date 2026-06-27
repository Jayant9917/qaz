"""Model gateway tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from novo.core.config import get_settings
from novo.models.gateway import generate_model_reply
from novo.models.registry import ModelCatalog


@pytest.mark.asyncio
async def test_openrouter_gateway_falls_back_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVO_OPENROUTER_API_KEY", raising=False)
    get_settings.cache_clear()

    model = ModelCatalog(
        id=uuid4(),
        provider="openrouter",
        model_key="openrouter/free/fast",
        display_name="OpenRouter Free Fast",
        capabilities={"fast_path": True},
        context_window=8192,
        max_output_tokens=2048,
        privacy_eligibility="private",
        pricing={"input_minor": 0, "output_minor": 0, "currency": "USD"},
        enabled=True,
    )

    reply = await generate_model_reply(
        model=model,
        user_message="my api_key is sk-abcdef1234567890",
        prompt_version="conversation.reply.v1",
        system_prompt=(
            "You are NOVO, the owner-first AI OS. "
            "Respond calmly, directly, and helpfully."
        ),
    )

    assert reply.used_fallback is True
    assert reply.provider_name == "openrouter"
    assert reply.model_key == "openrouter/free/fast"
    assert "sk-" not in reply.safe_text
    assert reply.findings
    get_settings.cache_clear()
