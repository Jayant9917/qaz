"""Local NOVO desktop settings without secrets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path

DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 820


@dataclass(frozen=True, slots=True)
class DesktopSettings:
    backend_url: str = DEFAULT_BACKEND_URL
    email: str = ""
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT


def settings_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / "NOVO"
    return Path.home() / ".novo"


def settings_file() -> Path:
    return settings_dir() / "desktop_settings.json"


def load_desktop_settings() -> DesktopSettings:
    path = settings_file()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return DesktopSettings()
    except Exception:
        return DesktopSettings()

    if not isinstance(raw, dict):
        return DesktopSettings()

    backend_url = str(raw.get("backend_url") or DEFAULT_BACKEND_URL).strip() or DEFAULT_BACKEND_URL
    email = str(raw.get("email") or "").strip()
    try:
        window_width = int(raw.get("window_width") or DEFAULT_WINDOW_WIDTH)
    except (TypeError, ValueError):
        window_width = DEFAULT_WINDOW_WIDTH
    try:
        window_height = int(raw.get("window_height") or DEFAULT_WINDOW_HEIGHT)
    except (TypeError, ValueError):
        window_height = DEFAULT_WINDOW_HEIGHT

    return DesktopSettings(
        backend_url=backend_url,
        email=email,
        window_width=max(1100, window_width),
        window_height=max(720, window_height),
    )


def save_desktop_settings(settings: DesktopSettings) -> None:
    path = settings_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2, ensure_ascii=True), encoding="utf-8")
