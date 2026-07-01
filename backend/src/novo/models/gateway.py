"""Provider-neutral model gateway for NOVO."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Sequence
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

logger = logging.getLogger(__name__)

MAX_RESPONSE_SNIPPET_CHARS = 2000


@dataclass(slots=True)
class GatewayStreamChunk:
    token: str = ""
    done: bool = False
    safe_text: str = ""
    findings: list[GuardrailFinding] | None = None
    provider_request_id: str | None = None
    provider_name: str = ""
    model_key: str = ""
    used_fallback: bool = False
    fallback_reason: str | None = None
    fallback_detail_safe: str | None = None
    attempts: int = 1
    finish_reason: str | None = None


@dataclass(slots=True)
class GatewayReply:
    safe_text: str
    findings: list[GuardrailFinding]
    provider_request_id: str | None
    provider_name: str
    model_key: str
    used_fallback: bool
    fallback_reason: str | None = None
    fallback_detail_safe: str | None = None
    attempts: int = 1
    finish_reason: str | None = None


def _candidate_models(
    primary_model: ModelCatalog,
    fallback_models: Sequence[ModelCatalog] | None,
) -> list[ModelCatalog]:
    ordered: list[ModelCatalog] = [primary_model]
    seen = {(primary_model.provider, primary_model.model_key)}
    for model in fallback_models or []:
        key = (model.provider, model.model_key)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(model)
    return ordered


def _classify_http_failure(status_code: int, body_text: str) -> str:
    lowered = body_text.casefold()
    if status_code == 429 or "rate limit" in lowered:
        return "rate_limit"
    if (
        "maximum context length" in lowered
        or "max_tokens" in lowered
        or "context length" in lowered
    ):
        return "token_limit"
    if status_code == 401:
        return "openrouter_auth_failed"
    if status_code == 403:
        return "openrouter_forbidden"
    if 500 <= status_code <= 599:
        return "openrouter_provider_error"
    return "openrouter_api_error"


async def _attempt_openrouter_model(
    *,
    model: ModelCatalog,
    sanitized_user_message: str,
    prompt_version: str,
    system_prompt: str,
    timeout_seconds: float,
) -> GatewayReply:
    system_message = system_prompt
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
        "Content-Type": "application/json",
        "HTTP-Referer": get_settings().frontend_origin,
        "X-Title": get_settings().app_name,
    }

    settings = get_settings()
    if settings.openrouter_api_key:
        headers["Authorization"] = f"Bearer {settings.openrouter_api_key}"

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=request_payload,
            )
    except httpx.TimeoutException:
        logger.error(
            "openrouter_failed",
            extra={
                "status_code": None,
                "model": model.model_key,
                "fallback_reason": "openrouter_timeout",
            },
        )
        return GatewayReply(
            safe_text="",
            findings=[],
            provider_request_id=None,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason="openrouter_timeout",
            fallback_detail_safe="Request timed out before OpenRouter responded.",
        )
    except httpx.RequestError as exc:
        logger.error(
            "openrouter_failed",
            extra={
                "status_code": None,
                "model": model.model_key,
                "fallback_reason": "openrouter_network_error",
                "error_type": exc.__class__.__name__,
            },
        )
        return GatewayReply(
            safe_text="",
            findings=[],
            provider_request_id=None,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason="openrouter_network_error",
            fallback_detail_safe="Network error while calling OpenRouter.",
        )
    except Exception:
        logger.exception(
            "openrouter_failed",
            extra={
                "status_code": None,
                "model": model.model_key,
                "fallback_reason": "openrouter_unexpected_error",
            },
        )
        return GatewayReply(
            safe_text="",
            findings=[],
            provider_request_id=None,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason="openrouter_unexpected_error",
            fallback_detail_safe="Unexpected error while calling OpenRouter.",
        )

    provider_request_id = response.headers.get("x-request-id")
    if provider_request_id is not None:
        provider_request_id = str(provider_request_id)
    response_snippet = response.text[:MAX_RESPONSE_SNIPPET_CHARS]

    if not response.is_success:
        failure_reason = _classify_http_failure(response.status_code, response_snippet)
        logger.error(
            "openrouter_failed",
            extra={
                "status_code": response.status_code,
                "model": model.model_key,
                "provider_request_id": provider_request_id,
                "fallback_reason": failure_reason,
                "response_snippet": response_snippet,
            },
        )
        return GatewayReply(
            safe_text="",
            findings=[],
            provider_request_id=provider_request_id,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=failure_reason,
            fallback_detail_safe=f"OpenRouter returned HTTP {response.status_code}.",
        )

    try:
        payload = response.json()
    except ValueError:
        logger.error(
            "openrouter_failed",
            extra={
                "status_code": response.status_code,
                "model": model.model_key,
                "provider_request_id": provider_request_id,
                "fallback_reason": "invalid_json",
                "response_snippet": response_snippet,
            },
        )
        return GatewayReply(
            safe_text="",
            findings=[],
            provider_request_id=provider_request_id,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason="invalid_json",
            fallback_detail_safe="OpenRouter returned invalid JSON.",
        )

    finish_reason = None
    usage = None
    text = ""
    provider_error_text = ""
    if isinstance(payload, dict):
        usage = payload.get("usage")
        choices = payload.get("choices") or []
        if choices:
            first_choice = choices[0] or {}
            finish_reason = str(first_choice.get("finish_reason") or "") or None
            message = first_choice.get("message") or {}
            text = str(message.get("content") or "").strip()
        if not text and payload.get("error"):
            error_payload = payload.get("error")
            if isinstance(error_payload, dict):
                provider_error_text = str(
                    error_payload.get("message") or error_payload.get("code") or ""
                )
            else:
                provider_error_text = str(error_payload)

    if finish_reason == "length":
        logger.warning(
            "openrouter_truncated",
            extra={
                "model": model.model_key,
                "provider_request_id": provider_request_id,
                "finish_reason": finish_reason,
                "usage": usage,
            },
        )

    if not text:
        failure_reason = "empty_response"
        if provider_error_text:
            failure_reason = _classify_http_failure(response.status_code, provider_error_text)
        logger.error(
            "openrouter_failed",
            extra={
                "status_code": response.status_code,
                "model": model.model_key,
                "provider_request_id": provider_request_id,
                "fallback_reason": failure_reason,
                "response_snippet": response_snippet,
            },
        )
        return GatewayReply(
            safe_text="",
            findings=[],
            provider_request_id=provider_request_id,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=failure_reason,
            fallback_detail_safe=provider_error_text or "OpenRouter returned an empty response.",
            finish_reason=finish_reason,
        )

    findings = inspect_text(text)
    if findings:
        safe_text = redact_sensitive_text(text).strip()
        if not safe_text:
            logger.error(
                "openrouter_failed",
                extra={
                    "status_code": response.status_code,
                    "model": model.model_key,
                    "provider_request_id": provider_request_id,
                    "fallback_reason": "empty_response_after_redaction",
                    "response_snippet": response_snippet,
                },
            )
            return GatewayReply(
                safe_text="",
                findings=[],
                provider_request_id=provider_request_id,
                provider_name=model.provider,
                model_key=model.model_key,
                used_fallback=True,
                fallback_reason="empty_response_after_redaction",
                fallback_detail_safe="OpenRouter response was fully redacted.",
                finish_reason=finish_reason,
            )
        logger.info(
            "openrouter_success",
            extra={
                "model": model.model_key,
                "provider_request_id": provider_request_id,
                "finish_reason": finish_reason,
                "usage": usage,
                "redacted_output": True,
            },
        )
        return GatewayReply(
            safe_text=safe_text,
            findings=findings,
            provider_request_id=provider_request_id,
            provider_name=model.provider,
            model_key=model.model_key,
            used_fallback=False,
            finish_reason=finish_reason,
        )

    logger.info(
        "openrouter_success",
        extra={
            "model": model.model_key,
            "provider_request_id": provider_request_id,
            "finish_reason": finish_reason,
            "usage": usage,
            "redacted_output": False,
        },
    )
    return GatewayReply(
        safe_text=text,
        findings=[],
        provider_request_id=provider_request_id,
        provider_name=model.provider,
        model_key=model.model_key,
        used_fallback=False,
        finish_reason=finish_reason,
    )


async def generate_model_reply(
    *,
    model: ModelCatalog,
    user_message: str,
    prompt_version: str,
    system_prompt: str,
    fallback_models: Sequence[ModelCatalog] | None = None,
) -> GatewayReply:
    settings = get_settings()


    if model.provider != "openrouter" or not settings.openrouter_api_key:
        fallback = build_stub_reply(user_message, fallback_reason="missing_api_key")
        return GatewayReply(
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=None,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason="missing_api_key",
            fallback_detail_safe="OpenRouter API key is missing or the provider is disabled.",
        )

    candidates = _candidate_models(model, fallback_models)
    last_reason = "openrouter_unavailable"
    last_detail = "OpenRouter was unavailable."
    last_provider_request_id: str | None = None

    for attempt_index, candidate in enumerate(candidates, start=1):
        if candidate.provider != "openrouter":
            continue

        final_chunk: GatewayStreamChunk | None = None
        async for chunk in stream_model_reply(
            model=candidate,
            user_message=user_message,
            prompt_version=prompt_version,
            system_prompt=system_prompt,
        ):
            if chunk.done:
                final_chunk = chunk

        if final_chunk is not None and final_chunk.safe_text.strip() and not final_chunk.used_fallback:
            return GatewayReply(
                safe_text=final_chunk.safe_text,
                findings=final_chunk.findings or [],
                provider_request_id=final_chunk.provider_request_id,
                provider_name=final_chunk.provider_name,
                model_key=final_chunk.model_key,
                used_fallback=False,
                fallback_reason=final_chunk.fallback_reason,
                fallback_detail_safe=final_chunk.fallback_detail_safe,
                attempts=final_chunk.attempts,
                finish_reason=final_chunk.finish_reason,
            )

        if final_chunk is not None:
            last_reason = final_chunk.fallback_reason or last_reason
            last_detail = final_chunk.fallback_detail_safe or last_detail
            last_provider_request_id = final_chunk.provider_request_id or last_provider_request_id
        if attempt_index < len(candidates):
            logger.warning(
                "openrouter_retrying",
                extra={
                    "attempt": attempt_index,
                    "model": candidate.model_key,
                    "fallback_reason": last_reason,
                },
            )

    fallback = build_stub_reply(user_message, fallback_reason=last_reason)
    return GatewayReply(
        safe_text=fallback.safe_text,
        findings=fallback.findings,
        provider_request_id=last_provider_request_id,
        provider_name="fallback",
        model_key=model.model_key,
        used_fallback=True,
        fallback_reason=last_reason,
        fallback_detail_safe=last_detail,
        attempts=len(candidates),
    )

async def _stream_openrouter_model(
    *,
    model: ModelCatalog,
    sanitized_user_message: str,
    prompt_version: str,
    system_prompt: str,
    timeout_seconds: float,
) -> AsyncIterator[GatewayStreamChunk]:
    system_message = system_prompt
    request_payload = {
        "model": model.model_key,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": sanitized_user_message},
        ],
        "temperature": 0.2,
        "max_tokens": model.max_output_tokens,
        "stream": True,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "HTTP-Referer": get_settings().frontend_origin,
        "X-Title": get_settings().app_name,
    }

    settings = get_settings()
    if settings.openrouter_api_key:
        headers["Authorization"] = f"Bearer {settings.openrouter_api_key}"

    provider_request_id: str | None = None
    running_text: list[str] = []
    finish_reason: str | None = None

    try:
        async with (
            httpx.AsyncClient(timeout=timeout_seconds) as client,
            client.stream(
                "POST",
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=request_payload,
            ) as response,
        ):
                provider_request_id = response.headers.get("x-request-id")
                if provider_request_id is not None:
                    provider_request_id = str(provider_request_id)
                if not response.is_success:
                    body = (await response.aread()).decode("utf-8", errors="replace")
                    failure_reason = _classify_http_failure(response.status_code, body)
                    fallback = build_stub_reply(
                        sanitized_user_message,
                        fallback_reason=failure_reason,
                    )
                    for token in fallback.safe_text.split():
                        yield GatewayStreamChunk(token=token)
                    yield GatewayStreamChunk(
                        done=True,
                        safe_text=fallback.safe_text,
                        findings=fallback.findings,
                        provider_request_id=provider_request_id,
                        provider_name="fallback",
                        model_key=model.model_key,
                        used_fallback=True,
                        fallback_reason=failure_reason,
                        fallback_detail_safe=f"OpenRouter returned HTTP {response.status_code}.",
                    )
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data:"):
                        line = line.split(":", 1)[1].strip()
                    if line == "[DONE]":
                        break
                    try:
                        payload = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(payload, dict):
                        continue
                    choices = payload.get("choices") or []
                    if not choices:
                        continue
                    first_choice = choices[0] or {}
                    finish_reason = str(first_choice.get("finish_reason") or "") or finish_reason
                    delta = first_choice.get("delta") or {}
                    token = str(delta.get("content") or "")
                    if token:
                        running_text.append(token)
                        yield GatewayStreamChunk(token=token)
    except httpx.TimeoutException:
        fallback_reason = "openrouter_timeout"
        fallback = build_stub_reply(sanitized_user_message, fallback_reason=fallback_reason)
        for token in fallback.safe_text.split():
            yield GatewayStreamChunk(token=token)
        yield GatewayStreamChunk(
            done=True,
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=provider_request_id,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=fallback_reason,
            fallback_detail_safe="Request timed out before OpenRouter responded.",
        )
        return
    except httpx.RequestError:
        fallback_reason = "openrouter_network_error"
        fallback = build_stub_reply(sanitized_user_message, fallback_reason=fallback_reason)
        for token in fallback.safe_text.split():
            yield GatewayStreamChunk(token=token)
        yield GatewayStreamChunk(
            done=True,
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=provider_request_id,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=fallback_reason,
            fallback_detail_safe="Network error while calling OpenRouter.",
        )
        return
    except Exception:
        fallback_reason = "openrouter_unexpected_error"
        logger.exception(
            "openrouter_failed",
            extra={
                "status_code": None,
                "model": model.model_key,
                "provider_request_id": provider_request_id,
                "fallback_reason": fallback_reason,
            },
        )
        fallback = build_stub_reply(sanitized_user_message, fallback_reason=fallback_reason)
        for token in fallback.safe_text.split():
            yield GatewayStreamChunk(token=token)
        yield GatewayStreamChunk(
            done=True,
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=provider_request_id,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=fallback_reason,
            fallback_detail_safe="Unexpected error while streaming from OpenRouter.",
        )
        return

    raw_text = "".join(running_text).strip()
    if not raw_text:
        fallback_reason = "empty_response"
        fallback = build_stub_reply(sanitized_user_message, fallback_reason=fallback_reason)
        for token in fallback.safe_text.split():
            yield GatewayStreamChunk(token=token)
        yield GatewayStreamChunk(
            done=True,
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=provider_request_id,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=fallback_reason,
            fallback_detail_safe="OpenRouter returned an empty streaming response.",
            finish_reason=finish_reason,
        )
        return

    findings = inspect_text(raw_text)
    safe_text = redact_sensitive_text(raw_text).strip() if findings else raw_text
    if not safe_text:
        fallback_reason = "empty_response_after_redaction"
        fallback = build_stub_reply(sanitized_user_message, fallback_reason=fallback_reason)
        for token in fallback.safe_text.split():
            yield GatewayStreamChunk(token=token)
        yield GatewayStreamChunk(
            done=True,
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=provider_request_id,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason=fallback_reason,
            fallback_detail_safe="OpenRouter response was fully redacted.",
            finish_reason=finish_reason,
        )
        return

    yield GatewayStreamChunk(
        done=True,
        safe_text=safe_text,
        findings=findings,
        provider_request_id=provider_request_id,
        provider_name=model.provider,
        model_key=model.model_key,
        used_fallback=False,
        finish_reason=finish_reason,
    )


async def stream_model_reply(
    *,
    model: ModelCatalog,
    user_message: str,
    prompt_version: str,
    system_prompt: str,
) -> AsyncIterator[GatewayStreamChunk]:
    settings = get_settings()
    sanitized_user_message = redact_sensitive_text(user_message)
    if model.provider != "openrouter" or not settings.openrouter_api_key:
        fallback = build_stub_reply(user_message, fallback_reason="missing_api_key")
        for token in fallback.safe_text.split():
            yield GatewayStreamChunk(token=token)
        yield GatewayStreamChunk(
            done=True,
            safe_text=fallback.safe_text,
            findings=fallback.findings,
            provider_request_id=None,
            provider_name="fallback",
            model_key=model.model_key,
            used_fallback=True,
            fallback_reason="missing_api_key",
            fallback_detail_safe="OpenRouter API key is missing or the provider is disabled.",
        )
        return

    async for chunk in _stream_openrouter_model(
        model=model,
        sanitized_user_message=sanitized_user_message,
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        timeout_seconds=settings.openrouter_timeout_seconds,
    ):
        yield chunk







