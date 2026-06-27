"""Provider-neutral model gateway for NOVO."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from novo.conversations.guardrails import (
    GuardrailFinding,
    build_stub_reply,
    inspect_text,
    redact_sensitive_text,
)
from novo.core.config import get_settings
from novo.models.registry import ModelCatalog


@dataclass(slots=True)
class GatewayReply:
    safe_text: str
    findings: list[GuardrailFinding]
    provider_request_id: str | None
    provider_name: str
    model_key: str
    used_fallback: bool


async def generate_model_reply(
    *,
    model: ModelCatalog,
    user_message: str,
    prompt_version: str,
    system_prompt: str,
) -> GatewayReply:
    settings = get_settings()
    sanitized_user_message = redact_sensitive_text(user_message)

    if model.provider != "openrouter" or not settings.openrouter_api_key:
        fallback = build_stub_reply(user_message)
        return GatewayReply(
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=None,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
        )

    system_message = f"{system_prompt}\nPrompt version: {prompt_version}"
    request_payload = {
        "model": model.model_key,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": sanitized_user_message},
        ],
        "temperature": 0.2,
        "max_tokens": model.max_output_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.frontend_origin,
        "X-Title": settings.app_name,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
            response = await client.post(
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=request_payload,
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        fallback = build_stub_reply(user_message)
        return GatewayReply(
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=None,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
        )

    provider_request_id = None
    text = ""
    if isinstance(payload, dict):
        provider_request_id = payload.get("id") or response.headers.get("x-request-id")
        if provider_request_id is not None:
            provider_request_id = str(provider_request_id)
        choices = payload.get("choices") or []
        if choices:
            first_choice = choices[0] or {}
            message = first_choice.get("message") or {}
            text = str(message.get("content") or "").strip()

    if not text:
        fallback = build_stub_reply(user_message)
        return GatewayReply(
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=provider_request_id,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
        )

    findings = inspect_text(text)
    if findings:
        safe_text = redact_sensitive_text(text).strip()
        if not safe_text:
            fallback = build_stub_reply(user_message)
            return GatewayReply(
                safe_text=fallback.safe_text,
                findings=fallback.findings,
                provider_request_id=provider_request_id,
                provider_name=model.provider,
                model_key=model.model_key,
                used_fallback=True,
            )
        return GatewayReply(
            safe_text=safe_text,
            findings=findings,
            provider_request_id=provider_request_id,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=False,
        )

    return GatewayReply(
        safe_text=text,
        findings=[],
        provider_request_id=provider_request_id,
        provider_name=model.provider,
        model_key=model.model_key,
        used_fallback=False,
    )
