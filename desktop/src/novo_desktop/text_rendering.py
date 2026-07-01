"""Shared text rendering helpers for NOVO assistant replies."""

from __future__ import annotations

import html as html_lib
import re
from html.parser import HTMLParser

try:
    import markdown as markdown_lib
except Exception:  # noqa: BLE001
    markdown_lib = None


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _strip_markdown_syntax(text: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""

    cleaned = re.sub(r"```(?:[\w+-]+)?\n(.*?)```", r"\1", cleaned, flags=re.S)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.M)
    cleaned = re.sub(r"^\s*>\s?", "", cleaned, flags=re.M)
    cleaned = re.sub(r"^\s*[-*+]\s+", "- ", cleaned, flags=re.M)
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned, flags=re.M)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    cleaned = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


class _SpeechTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def _append_newline(self) -> None:
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag: str, _attrs) -> None:  # noqa: ANN001
        if tag in {"p", "div", "section", "article", "blockquote", "ul", "ol", "pre"}:
            self._append_newline()
        elif tag == "br":
            self._append_newline()
        elif tag == "li":
            self._append_newline()
            self.parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "section", "article", "blockquote", "li", "pre"}:
            self._append_newline()

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


def render_assistant_html(text: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    if markdown_lib is not None:
        return markdown_lib.markdown(cleaned, extensions=["extra", "sane_lists", "nl2br"])
    escaped = html_lib.escape(_strip_markdown_syntax(cleaned)).replace("\n", "<br>")
    return f"<div>{escaped}</div>"


def render_plain_html(text: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    escaped = html_lib.escape(cleaned).replace("\n", "<br>")
    return f"<div>{escaped}</div>"


def speech_text_from_assistant_markdown(text: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    if markdown_lib is not None:
        html_text = markdown_lib.markdown(cleaned, extensions=["extra", "sane_lists", "nl2br"])
        parser = _SpeechTextExtractor()
        parser.feed(html_text)
        return parser.get_text()
    return _strip_markdown_syntax(cleaned)
