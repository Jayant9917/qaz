"""Model gateway tests."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from novo.core.config import get_settings
from novo.models import gateway
from novo.models.gateway import generate_model_reply, stream_model_reply
from novo.models.registry import ModelCatalog


@pytest.mark.asyncio
async def test_openrouter_gateway_falls_back_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVO_OPENROUTER_API_KEY", "")
    get_settings.cache_clear()

    model = ModelCatalog(
        id=uuid4(),
        provider="openrouter",
        model_key="openrouter/free",
        display_name="OpenRouter Free Router",
        capabilities={"fast_path": True},
        context_window=8192,
        max_output_tokens=256,
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
    assert reply.provider_name == "fallback"
    assert reply.model_key == "openrouter/free"
    assert reply.fallback_reason == "missing_api_key"
    assert "Fallback used" in reply.safe_text
    assert "sk-" not in reply.safe_text
    assert reply.findings
    get_settings.cache_clear()



@pytest.mark.asyncio
async def test_stream_reply_yields_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVO_OPENROUTER_API_KEY", "")
    get_settings.cache_clear()

    model = ModelCatalog(
        id=uuid4(),
        provider="openrouter",
        model_key="openrouter/free",
        display_name="OpenRouter Free Router",
        capabilities={"fast_path": True, "streaming": True},
        context_window=8192,
        max_output_tokens=256,
        privacy_eligibility="private",
        pricing={"input_minor": 0, "output_minor": 0, "currency": "USD"},
        enabled=True,
    )

    chunks = [
        chunk
        async for chunk in stream_model_reply(
            model=model,
            user_message="Hello NOVO",
            prompt_version="conversation.reply.v1",
            system_prompt="You are NOVO.",
        )
    ]

    assert any(chunk.token for chunk in chunks)
    assert chunks[-1].done is True
    assert chunks[-1].used_fallback is True
    assert chunks[-1].fallback_reason == "missing_api_key"
    get_settings.cache_clear()

@pytest.mark.asyncio
async def test_openrouter_gateway_retries_before_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVO_OPENROUTER_API_KEY", "test-key")
    get_settings.cache_clear()

    primary_model = ModelCatalog(
        id=uuid4(),
        provider="openrouter",
        model_key="openrouter/free",
        display_name="OpenRouter Free Router",
        capabilities={"fast_path": True},
        context_window=8192,
        max_output_tokens=256,
        privacy_eligibility="private",
        pricing={"input_minor": 0, "output_minor": 0, "currency": "USD"},
        enabled=True,
    )
    fallback_model = ModelCatalog(
        id=uuid4(),
        provider="openrouter",
        model_key="openai/gpt-oss-120b:free",
        display_name="OpenAI GPT-OSS 120B (free)",
        capabilities={"fast_path": True, "deep_reasoning": True},
        context_window=131072,
        max_output_tokens=256,
        privacy_eligibility="private",
        pricing={"input_minor": 0, "output_minor": 0, "currency": "USD"},
        enabled=True,
    )

    async def fake_stream_model_reply(*, model, user_message, prompt_version, system_prompt):
        if model.model_key == primary_model.model_key:
            yield gateway.GatewayStreamChunk(token="Retry")
            yield gateway.GatewayStreamChunk(
                done=True,
                safe_text="",
                findings=[],
                provider_request_id="req-primary",
                provider_name=model.provider,
                model_key=model.model_key,
                used_fallback=True,
                fallback_reason="openrouter_timeout",
                fallback_detail_safe="Request timed out before OpenRouter responded.",
            )
            return

        yield gateway.GatewayStreamChunk(token="Hello")
        yield gateway.GatewayStreamChunk(
            done=True,
            safe_text="Hello from retry.",
            findings=[],
            provider_request_id="req-fallback",
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=False,
        )

    monkeypatch.setattr(gateway, "stream_model_reply", fake_stream_model_reply)

    reply = await generate_model_reply(
        model=primary_model,
        fallback_models=[fallback_model],
        user_message="Tell me something useful.",
        prompt_version="conversation.reply.v1",
        system_prompt=(
            "You are NOVO, the owner-first AI OS. "
            "Respond calmly, directly, and helpfully."
        ),
    )

    assert reply.used_fallback is False
    assert reply.safe_text == "Hello from retry."
    assert reply.provider_name == "openrouter"
    assert reply.model_key == fallback_model.model_key
    assert reply.attempts == 1
    get_settings.cache_clear()
