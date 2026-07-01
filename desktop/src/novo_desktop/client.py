"""Backend client for the NOVO Desktop Assistant."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import json
from http.cookiejar import CookieJar
from typing import Any
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener


class NovoApiError(RuntimeError):
    """Raised when the backend returns an error or cannot be reached."""


logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class SessionInfo:
    display_name: str
    email: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class ConversationInfo:
    id: str
    title: str


@dataclass(frozen=True, slots=True)
class ChatResponse:
    response_id: str
    user_message: str


@dataclass(frozen=True, slots=True)
class ResponseEvent:
    event: str
    data: dict[str, Any]


class NovoApiClient:
    """Small stdlib HTTP client for E2.5 desktop experiments."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/api/v1/"
        self.cookie_jar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookie_jar))
        self.csrf_token: str | None = None

    def health_live(self) -> dict[str, Any]:
        return self._request_json("GET", "health/live")

    def login(self, email: str, password: str) -> SessionInfo:
        payload = self._request_json(
            "POST",
            "auth/login",
            {"email": email, "password": password},
        )
        self.csrf_token = str(payload.get("csrf_token") or "")
        user = payload.get("user") or {}
        session = payload.get("session") or {}
        return SessionInfo(
            display_name=str(user.get("display_name") or user.get("email") or "Owner"),
            email=str(user.get("email") or email),
            expires_at=str(session.get("expires_at") or ""),
        )

    def me(self) -> SessionInfo:
        payload = self._request_json("GET", "auth/me")
        user = payload.get("user") or {}
        session = payload.get("session") or {}
        return SessionInfo(
            display_name=str(user.get("display_name") or user.get("email") or "Owner"),
            email=str(user.get("email") or ""),
            expires_at=str(session.get("expires_at") or ""),
        )

    def list_conversations(self) -> list[ConversationInfo]:
        payload = self._request_json("GET", "conversations")
        return [
            ConversationInfo(id=str(item["id"]), title=str(item["title"]))
            for item in payload.get("items", [])
        ]

    def create_conversation(self, title: str) -> ConversationInfo:
        payload = self._request_json(
            "POST",
            "conversations",
            {"title": title, "classification": "private"},
            csrf=True,
        )
        return ConversationInfo(id=str(payload["id"]), title=str(payload["title"]))

    def send_message(self, conversation_id: str, content: str) -> ChatResponse:
        payload = self._request_json(
            "POST",
            f"conversations/{conversation_id}/messages",
            {
                "content": content,
                "role": "user",
                "content_format": "text/plain",
                "classification": "private",
            },
            csrf=True,
        )
        message = payload.get("message") or {}
        return ChatResponse(
            response_id=str(payload["response_id"]),
            user_message=str(message.get("content") or content),
        )

    def stream_response_events(self, response_id: str) -> Iterator[ResponseEvent]:
        response = self._open("GET", f"conversations/responses/{response_id}/events")
        event_name = "message"
        data_lines: list[str] = []

        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                if data_lines:
                    try:
                        yield ResponseEvent(event=event_name, data=json.loads("".join(data_lines)))
                    except ValueError as exc:
                        logger.exception(
                            "NOVO backend stream returned invalid event data",
                            extra={"response_id": response_id, "event": event_name},
                        )
                        raise NovoApiError("Backend returned invalid streamed event data.") from exc
                event_name = "message"
                data_lines = []
                continue
            if line.startswith("event:"):
                event_name = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        csrf: bool = False,
        api_path: bool = True,
    ) -> dict[str, Any]:
        response = self._open(method, path, payload, csrf=csrf, api_path=api_path)
        body = response.read().decode("utf-8")
        if not body:
            return {}
        try:
            return json.loads(body)
        except ValueError as exc:
            logger.exception(
                "NOVO backend returned invalid JSON",
                extra={"method": method, "path": path, "api_path": api_path},
            )
            raise NovoApiError(f"Backend returned invalid JSON from {path}.") from exc

    def _open(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        csrf: bool = False,
        api_path: bool = True,
    ):
        url = urljoin(self.api_base if api_path else f"{self.base_url}/", path.lstrip("/"))
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json", "User-Agent": "NOVO Desktop Assistant E2.5"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if csrf:
            if not self.csrf_token:
                raise NovoApiError("Sign in before making protected requests.")
            headers["X-CSRF-Token"] = self.csrf_token

        request = Request(url, data=data, headers=headers, method=method)
        try:
            return self.opener.open(request, timeout=60)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.exception(
                "NOVO API request failed",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": exc.code,
                    "detail": detail[:2000],
                },
            )
            raise NovoApiError(f"Backend returned {exc.code}: {detail}") from exc
        except URLError as exc:
            logger.exception(
                "NOVO backend unreachable",
                extra={"method": method, "path": path, "reason": str(exc.reason)},
            )
            raise NovoApiError(f"Could not reach NOVO backend at {self.base_url}: {exc.reason}") from exc