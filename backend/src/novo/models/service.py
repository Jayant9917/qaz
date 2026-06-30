"""Model and prompt registry services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import Integer, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from novo.conversations.responses import ResponseRun
from novo.models.registry import (
    ModelCatalog,
    ModelPolicy,
    PromptBinding,
    PromptTemplate,
    PromptVersion,
)

DEFAULT_MODEL_POLICY_NAME = "conversation.fast-path.default"
DEFAULT_PROMPT_KEY = "conversation.reply"

DEFAULT_MODEL_CATALOG_SEEDS = [
    {
        "provider": "openrouter",
        "model_key": "openrouter/free",
        "display_name": "OpenRouter Free Router",
        "capabilities": {"fast_path": True, "streaming": True, "structured_output": True},
        "context_window": 131072,
        "max_output_tokens": 256,
        "privacy_eligibility": "private",
        "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
        "enabled": True,
    },
    {
        "provider": "openrouter",
        "model_key": "openai/gpt-oss-120b:free",
        "display_name": "OpenAI GPT-OSS 120B (free)",
        "capabilities": {
            "fast_path": True,
            "deep_reasoning": True,
            "streaming": True,
            "structured_output": True,
        },
        "context_window": 131072,
        "max_output_tokens": 256,
        "privacy_eligibility": "private",
        "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
        "enabled": True,
    },
    {
        "provider": "openrouter",
        "model_key": "google/gemma-4-31b-it:free",
        "display_name": "Google Gemma 4 31B IT (free)",
        "capabilities": {
            "fast_path": True,
            "deep_reasoning": True,
            "streaming": True,
            "structured_output": True,
        },
        "context_window": 262144,
        "max_output_tokens": 256,
        "privacy_eligibility": "private",
        "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
        "enabled": True,
    },
    {
        "provider": "openrouter",
        "model_key": "poolside/laguna-m1:free",
        "display_name": "Poolside Laguna M1 (free)",
        "capabilities": {
            "fast_path": True,
            "deep_reasoning": True,
            "streaming": True,
            "structured_output": True,
        },
        "context_window": 262144,
        "max_output_tokens": 256,
        "privacy_eligibility": "private",
        "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
        "enabled": True,
    },
    {
        "provider": "stub",
        "model_key": "stub/echo",
        "display_name": "Stub Echo",
        "capabilities": {"fast_path": True, "streaming": True},
        "context_window": 4096,
        "max_output_tokens": 1024,
        "privacy_eligibility": "public",
        "pricing": {"input_minor": 0, "output_minor": 0, "currency": "USD"},
        "enabled": True,
    },
]

LEGACY_MODEL_KEY_ALIASES = {
    "openrouter/fusion": "openrouter/free",
    "openrouter/free/fast": "openrouter/free",
    "openrouter/free/deep": "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.2-3b-instruct:free": "openrouter/free",
}

DEFAULT_PROMPT_DEFINITION = {
    "prompt_key": DEFAULT_PROMPT_KEY,
    "purpose": "conversation.reply",
    "name": "Conversation reply",
    "description": "Default NOVO fast-path prompt for assistant chat replies.",
    "variable_schema": {
        "type": "object",
        "properties": {
            "owner_name": {"type": "string"},
            "conversation_title": {"type": "string"},
            "message": {"type": "string"},
        },
        "required": ["message"],
        "additionalProperties": False,
    },
    "security_level": "private",
    "content": (
        "You are NOVO, the owner-first AI OS. Respond calmly, directly, and helpfully. "
        "Write in plain text with short paragraphs. If you use headings, put them on their own line "
        "without markdown symbols like ### or **. Use simple hyphen bullets only when helpful. "
        "Avoid dense markdown formatting unless the user explicitly asks for it."
    ),
}


@dataclass(slots=True)
class RouteSelection:
    path: str
    route_reason: str
    prompt_version: str
    model_provider: str
    model_name: str
    model_id: UUID | None = None
    prompt_binding_id: UUID | None = None
    model_policy_id: UUID | None = None
    prompt_template_id: UUID | None = None
    prompt_version_id: UUID | None = None


async def ensure_model_registry_seed(db: AsyncSession, owner_id: UUID) -> None:
    existing_models = list(await db.scalars(select(ModelCatalog)))
    models_by_key = {model.model_key: model for model in existing_models}

    for legacy_key, real_key in LEGACY_MODEL_KEY_ALIASES.items():
        legacy_model = models_by_key.get(legacy_key)
        if legacy_model is None:
            continue
        seed = next(seed for seed in DEFAULT_MODEL_CATALOG_SEEDS if seed["model_key"] == real_key)
        legacy_model.provider = seed["provider"]
        legacy_model.model_key = seed["model_key"]
        legacy_model.display_name = seed["display_name"]
        legacy_model.capabilities = seed["capabilities"]
        legacy_model.context_window = seed["context_window"]
        legacy_model.max_output_tokens = seed["max_output_tokens"]
        legacy_model.privacy_eligibility = seed["privacy_eligibility"]
        legacy_model.pricing = seed["pricing"]
        legacy_model.enabled = seed["enabled"]

    await db.flush()
    models_by_key = {model.model_key: model for model in await db.scalars(select(ModelCatalog))}

    for seed in DEFAULT_MODEL_CATALOG_SEEDS:
        model = models_by_key.get(seed["model_key"])
        if model is None:
            db.add(ModelCatalog(**seed))
            await db.flush()
        else:
            model.display_name = seed["display_name"]
            model.capabilities = seed["capabilities"]
            model.context_window = seed["context_window"]
            model.max_output_tokens = seed["max_output_tokens"]
            model.privacy_eligibility = seed["privacy_eligibility"]
            model.pricing = seed["pricing"]
            model.enabled = seed["enabled"]

    policy = await db.scalar(
        select(ModelPolicy).where(
            ModelPolicy.owner_id == owner_id,
            ModelPolicy.name == DEFAULT_MODEL_POLICY_NAME,
        )
    )
    default_rules = {
        "route": "fast",
        "purpose": "conversation.reply",
        "preferred_model_keys": [
            "openrouter/free",
            "openai/gpt-oss-120b:free",
            "google/gemma-4-31b-it:free",
            "poolside/laguna-m1:free",
            "stub/echo",
        ],
        "fallback_model_key": "stub/echo",
        "fallback_allowed": True,
    }
    if policy is None:
        policy = ModelPolicy(
            owner_id=owner_id,
            name=DEFAULT_MODEL_POLICY_NAME,
            rules=default_rules,
            max_classification="private",
            max_cost_minor=0,
            currency="USD",
            latency_target_ms=5000,
            fallback_allowed=True,
            enabled=True,
        )
        db.add(policy)
        await db.flush()
    else:
        rules = dict(policy.rules or {})
        preferred_keys = [
            LEGACY_MODEL_KEY_ALIASES.get(str(item), str(item))
            for item in rules.get("preferred_model_keys", default_rules["preferred_model_keys"])
            if item
        ]
        if not preferred_keys:
            preferred_keys = default_rules["preferred_model_keys"]
        fallback_key = LEGACY_MODEL_KEY_ALIASES.get(
            str(rules.get("fallback_model_key", default_rules["fallback_model_key"])),
            str(rules.get("fallback_model_key", default_rules["fallback_model_key"])),
        )
        normalized_rules = {
            **rules,
            "route": rules.get("route", default_rules["route"]),
            "purpose": rules.get("purpose", default_rules["purpose"]),
            "preferred_model_keys": preferred_keys,
            "fallback_model_key": fallback_key,
            "fallback_allowed": bool(rules.get("fallback_allowed", True)),
        }
        if normalized_rules != rules:
            policy.rules = normalized_rules
        if not policy.enabled:
            policy.enabled = True


async def ensure_prompt_registry_seed(db: AsyncSession) -> None:
    template = await db.scalar(
        select(PromptTemplate).where(PromptTemplate.prompt_key == DEFAULT_PROMPT_KEY)
    )
    if template is None:
        template = PromptTemplate(
            **{k: v for k, v in DEFAULT_PROMPT_DEFINITION.items() if k != "content"}
        )
        db.add(template)
        await db.flush()

    version = await db.scalar(
        select(PromptVersion).where(
            PromptVersion.template_id == template.id,
            PromptVersion.version_no == 1,
        )
    )
    if version is None:
        version = PromptVersion(
            template_id=template.id,
            version_no=1,
            content=DEFAULT_PROMPT_DEFINITION["content"],
            content_hash=sha256(DEFAULT_PROMPT_DEFINITION["content"].encode("utf-8")).hexdigest(),
            status="active",
            change_reason="Initial fast-path prompt seed",
            evaluation_status="passed",
            activated_at=datetime.now(UTC),
        )
        db.add(version)
        await db.flush()

    binding = await db.scalar(
        select(PromptBinding).where(
            PromptBinding.purpose == "conversation.reply",
            PromptBinding.owner_id.is_(None),
            PromptBinding.prompt_version_id == version.id,
        )
    )
    if binding is None:
        binding = PromptBinding(
            owner_id=None,
            purpose="conversation.reply",
            agent_type=None,
            tool_capability_id=None,
            prompt_version_id=version.id,
            priority=1,
            valid_from=datetime.now(UTC),
            valid_until=None,
        )
        db.add(binding)
        await db.flush()


async def list_models(db: AsyncSession) -> list[ModelCatalog]:
    result = await db.scalars(
        select(ModelCatalog).order_by(ModelCatalog.provider.asc(), ModelCatalog.model_key.asc())
    )
    return list(result)


async def get_model(db: AsyncSession, model_id: UUID) -> ModelCatalog | None:
    return await db.scalar(select(ModelCatalog).where(ModelCatalog.id == model_id))


async def list_model_policies(db: AsyncSession, owner_id: UUID) -> list[ModelPolicy]:
    result = await db.scalars(
        select(ModelPolicy)
        .where(ModelPolicy.owner_id == owner_id)
        .order_by(
            ModelPolicy.enabled.desc(),
            ModelPolicy.updated_at.desc(),
            ModelPolicy.created_at.desc(),
        )
    )
    return list(result)


async def get_model_policy(db: AsyncSession, owner_id: UUID, policy_id: UUID) -> ModelPolicy | None:
    return await db.scalar(
        select(ModelPolicy).where(ModelPolicy.id == policy_id, ModelPolicy.owner_id == owner_id)
    )


async def create_model_policy(
    db: AsyncSession,
    *,
    owner_id: UUID,
    name: str,
    rules: dict[str, Any],
    max_classification: str,
    max_cost_minor: int,
    currency: str,
    latency_target_ms: int,
    fallback_allowed: bool,
    enabled: bool,
) -> ModelPolicy:
    policy = ModelPolicy(
        owner_id=owner_id,
        name=name,
        rules=rules,
        max_classification=max_classification,
        max_cost_minor=max_cost_minor,
        currency=currency,
        latency_target_ms=latency_target_ms,
        fallback_allowed=fallback_allowed,
        enabled=enabled,
    )
    db.add(policy)
    await db.flush()
    return policy


async def list_prompt_templates(db: AsyncSession) -> list[PromptTemplate]:
    result = await db.scalars(select(PromptTemplate).order_by(PromptTemplate.prompt_key.asc()))
    return list(result)


async def get_prompt_template(db: AsyncSession, template_id: UUID) -> PromptTemplate | None:
    return await db.scalar(select(PromptTemplate).where(PromptTemplate.id == template_id))


async def get_prompt_template_by_key(db: AsyncSession, prompt_key: str) -> PromptTemplate | None:
    return await db.scalar(select(PromptTemplate).where(PromptTemplate.prompt_key == prompt_key))


async def list_prompt_versions(db: AsyncSession, template_id: UUID) -> list[PromptVersion]:
    result = await db.scalars(
        select(PromptVersion)
        .where(PromptVersion.template_id == template_id)
        .order_by(PromptVersion.version_no.desc())
    )
    return list(result)


async def get_prompt_version(db: AsyncSession, version_id: UUID) -> PromptVersion | None:
    return await db.scalar(select(PromptVersion).where(PromptVersion.id == version_id))


async def create_prompt_version(
    db: AsyncSession,
    *,
    template: PromptTemplate,
    content: str,
    change_reason: str | None,
    created_by: UUID | None,
) -> PromptVersion:
    version_no = await db.scalar(
        select(func.coalesce(func.max(PromptVersion.version_no), 0)).where(
            PromptVersion.template_id == template.id
        )
    )
    version = PromptVersion(
        template_id=template.id,
        version_no=int(version_no or 0) + 1,
        content=content,
        content_hash=sha256(content.encode("utf-8")).hexdigest(),
        status="draft",
        change_reason=change_reason,
        created_by=created_by,
        evaluation_status="pending",
    )
    db.add(version)
    await db.flush()
    return version


async def list_prompt_bindings(
    db: AsyncSession, owner_id: UUID | None = None
) -> list[PromptBinding]:
    statement = select(PromptBinding)
    if owner_id is not None:
        statement = statement.where(
            (PromptBinding.owner_id == owner_id) | PromptBinding.owner_id.is_(None)
        )
    result = await db.scalars(
        statement.order_by(PromptBinding.priority.asc(), PromptBinding.created_at.desc())
    )
    return list(result)


async def get_prompt_binding(db: AsyncSession, binding_id: UUID) -> PromptBinding | None:
    return await db.scalar(select(PromptBinding).where(PromptBinding.id == binding_id))


async def update_prompt_binding(
    db: AsyncSession,
    binding: PromptBinding,
    *,
    prompt_version_id: UUID | None = None,
    priority: int | None = None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> PromptBinding:
    if prompt_version_id is not None:
        binding.prompt_version_id = prompt_version_id
    if priority is not None:
        binding.priority = priority
    if valid_from is not None:
        binding.valid_from = valid_from
    if valid_until is not None:
        binding.valid_until = valid_until
    await db.flush()
    return binding


async def evaluate_prompt_version(db: AsyncSession, version: PromptVersion) -> PromptVersion:
    lowered = version.content.casefold()
    secret_markers = ("api_key", "secret=", "password=", "token=", "sk-")
    version.evaluation_status = (
        "failed" if any(marker in lowered for marker in secret_markers) else "passed"
    )
    await db.flush()
    return version


async def activate_prompt_version(db: AsyncSession, version: PromptVersion) -> PromptVersion:
    other_versions = await db.scalars(
        select(PromptVersion).where(
            PromptVersion.template_id == version.template_id,
            PromptVersion.id != version.id,
            PromptVersion.status == "active",
        )
    )
    for other in other_versions:
        other.status = "retired"
        other.retired_at = datetime.now(UTC)
    version.status = "active"
    version.activated_at = datetime.now(UTC)
    version.retired_at = None
    await db.flush()
    return version


async def retire_prompt_version(db: AsyncSession, version: PromptVersion) -> PromptVersion:
    version.status = "retired"
    version.retired_at = datetime.now(UTC)
    await db.flush()
    return version


async def _resolve_prompt_version(
    db: AsyncSession,
    *,
    owner_id: UUID,
    purpose: str,
) -> tuple[PromptTemplate, PromptVersion, PromptBinding | None]:
    binding = await db.scalar(
        select(PromptBinding)
        .where(
            or_(PromptBinding.owner_id == owner_id, PromptBinding.owner_id.is_(None)),
            PromptBinding.purpose == purpose,
            or_(PromptBinding.valid_from.is_(None), PromptBinding.valid_from <= func.now()),
            or_(PromptBinding.valid_until.is_(None), PromptBinding.valid_until > func.now()),
        )
        .order_by(
            PromptBinding.owner_id.is_(None),
            PromptBinding.priority.asc(),
            PromptBinding.created_at.desc(),
        )
    )
    template = await db.scalar(select(PromptTemplate).where(PromptTemplate.prompt_key == purpose))
    if template is None:
        template = await db.scalar(
            select(PromptTemplate).where(PromptTemplate.prompt_key == DEFAULT_PROMPT_KEY)
        )
    if template is None:
        raise RuntimeError("Prompt registry seed is missing")

    if binding is not None:
        version = await get_prompt_version(db, binding.prompt_version_id)
        if version is None:
            raise RuntimeError("Prompt binding points to a missing version")
        return template, version, binding

    version = await db.scalar(
        select(PromptVersion)
        .where(PromptVersion.template_id == template.id, PromptVersion.status == "active")
        .order_by(PromptVersion.version_no.desc())
    )
    if version is None:
        version = await db.scalar(
            select(PromptVersion)
            .where(PromptVersion.template_id == template.id)
            .order_by(PromptVersion.version_no.desc())
        )
    if version is None:
        raise RuntimeError("Prompt registry seed is missing a version")
    return template, version, None


async def _resolve_model_policy(
    db: AsyncSession,
    *,
    owner_id: UUID,
    policy_id: UUID | None,
) -> ModelPolicy | None:
    if policy_id is not None:
        return await get_model_policy(db, owner_id, policy_id)
    return await db.scalar(
        select(ModelPolicy)
        .where(ModelPolicy.owner_id == owner_id, ModelPolicy.enabled.is_(True))
        .order_by(ModelPolicy.updated_at.desc(), ModelPolicy.created_at.desc())
    )


async def _select_model(
    db: AsyncSession,
    *,
    policy: ModelPolicy | None,
    classification: str,
    route_mode: str,
) -> ModelCatalog:
    models = list(await db.scalars(select(ModelCatalog).where(ModelCatalog.enabled.is_(True))))
    if not models:
        raise RuntimeError("No enabled models are registered")

    preferred_keys: list[str] = []
    fallback_key: str | None = None
    if policy is not None:
        preferred_keys = [
            str(item) for item in policy.rules.get("preferred_model_keys", []) if item
        ]
        fallback_key = policy.rules.get("fallback_model_key")

    def eligible(model: ModelCatalog) -> bool:
        if classification == "restricted" and model.privacy_eligibility != "restricted":
            return False
        if classification in {"secret", "confidential"} and model.privacy_eligibility == "public":
            return False
        if route_mode == "deep":
            return bool(model.capabilities.get("deep_reasoning")) or model.context_window >= 16000
        return bool(model.capabilities.get("fast_path", True))

    for preferred_key in preferred_keys:
        preferred = next(
            (model for model in models if model.model_key == preferred_key and eligible(model)),
            None,
        )
        if preferred is not None:
            return preferred

    eligible_models = [model for model in models if eligible(model)]
    if eligible_models:
        eligible_models.sort(
            key=lambda item: (
                item.pricing.get("input_minor", 0),
                item.pricing.get("output_minor", 0),
                -item.context_window,
                item.provider,
                item.model_key,
            )
        )
        return eligible_models[0]

    if fallback_key is not None:
        fallback = next((model for model in models if model.model_key == fallback_key), None)
        if fallback is not None:
            return fallback

    return models[0]


async def resolve_route_selection(
    db: AsyncSession,
    *,
    owner_id: UUID,
    classification: str,
    purpose: str = DEFAULT_PROMPT_KEY,
    route_mode: str = "fast",
    model_policy_id: UUID | None = None,
) -> RouteSelection:
    policy = await _resolve_model_policy(db, owner_id=owner_id, policy_id=model_policy_id)
    template, version, binding = await _resolve_prompt_version(
        db, owner_id=owner_id, purpose=purpose
    )
    model = await _select_model(
        db, policy=policy, classification=classification, route_mode=route_mode
    )
    reason_parts = [
        f"purpose={purpose}",
        f"path={route_mode}",
        f"prompt={template.prompt_key}.v{version.version_no}",
        f"model={model.provider}/{model.model_key}",
    ]
    if policy is not None:
        reason_parts.insert(1, f"policy={policy.name}")
    if binding is not None:
        reason_parts.append(f"binding={binding.id}")
    return RouteSelection(
        path=route_mode,
        route_reason="; ".join(reason_parts),
        prompt_version=f"{template.prompt_key}.v{version.version_no}",
        model_provider=model.provider,
        model_name=model.model_key,
        model_id=model.id,
        prompt_binding_id=binding.id if binding is not None else None,
        model_policy_id=policy.id if policy is not None else None,
        prompt_template_id=template.id,
        prompt_version_id=version.id,
    )


async def list_model_usage(db: AsyncSession) -> list[dict[str, object]]:
    rows = await db.execute(
        select(
            ResponseRun.model_provider,
            ResponseRun.model_name,
            func.count(ResponseRun.id),
            func.sum(ResponseRun.token_count),
            func.avg(ResponseRun.latency_ms),
            func.sum(func.cast(ResponseRun.status == "completed", Integer)),
        ).group_by(ResponseRun.model_provider, ResponseRun.model_name)
    )
    items: list[dict[str, object]] = []
    for provider, model_name, run_count, token_sum, avg_latency, success_sum in rows.all():
        run_count_int = int(run_count or 0)
        success_int = int(success_sum or 0)
        items.append(
            {
                "provider": provider,
                "model_name": model_name,
                "run_count": run_count_int,
                "token_count": int(token_sum or 0),
                "average_latency_ms": float(avg_latency) if avg_latency is not None else None,
                "success_count": success_int,
                "failure_count": run_count_int - success_int,
            }
        )
    return items


async def list_model_health(db: AsyncSession) -> list[dict[str, object]]:
    recent_runs = await db.execute(
        select(
            ResponseRun.model_provider,
            ResponseRun.model_name,
            func.count(ResponseRun.id),
            func.sum(func.cast(ResponseRun.status == "completed", Integer)),
            func.max(ResponseRun.completed_at),
        )
        .where(ResponseRun.created_at >= func.now() - text("INTERVAL '7 days'"))
        .group_by(ResponseRun.model_provider, ResponseRun.model_name)
    )
    usage_map: dict[tuple[str | None, str | None], tuple[int, int, datetime | None]] = {}
    for provider, model_name, run_count, success_count, last_run_at in recent_runs.all():
        usage_map[(provider, model_name)] = (
            int(run_count or 0),
            int(success_count or 0),
            last_run_at,
        )

    items: list[dict[str, object]] = []
    models = await list_models(db)
    for model in models:
        run_count, success_count, last_run_at = usage_map.get(
            (model.provider, model.model_key), (0, 0, None)
        )
        success_rate = (success_count / run_count) if run_count else None
        health_status = "healthy" if model.enabled else "disabled"
        if model.enabled and run_count and success_rate is not None and success_rate < 0.8:
            health_status = "degraded"
        items.append(
            {
                "model_id": model.id,
                "provider": model.provider,
                "model_key": model.model_key,
                "display_name": model.display_name,
                "enabled": model.enabled,
                "health_status": health_status,
                "recent_run_count": run_count,
                "recent_success_rate": success_rate,
                "last_run_at": last_run_at,
            }
        )
    return items
