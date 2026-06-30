from __future__ import annotations

import io
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novo_desktop.client import NovoApiClient


class FakeStreamingResponse(io.BytesIO):
    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if line == b"":
            raise StopIteration
        return line


class NovoApiClientTests(unittest.TestCase):
    def test_stream_response_events_parses_sse_events(self) -> None:
        client = NovoApiClient("http://localhost:8000")
        payload = (
            b"event: response.token\n"
            b"data: {\"token\":\"hello\",\"content\":\"hello\"}\n"
            b"\n"
            b"event: response.completed\n"
            b"data: {\"response_id\":\"r1\"}\n"
            b"\n"
        )
        client._open = lambda *args, **kwargs: FakeStreamingResponse(payload)  # type: ignore[method-assign]

        events = list(client.stream_response_events("r1"))

        self.assertEqual(events[0].event, "response.token")
        self.assertEqual(events[0].data["token"], "hello")
        self.assertEqual(events[1].event, "response.completed")

    def test_health_uses_api_prefixed_route(self) -> None:
        client = NovoApiClient("http://localhost:8000")
        calls: list[tuple[str, str, bool]] = []

        def fake_open(method: str, path: str, *args, **kwargs):
            calls.append((method, path, kwargs.get("api_path", True)))
            return io.BytesIO(b"{\"status\":\"alive\"}")

        client._open = fake_open  # type: ignore[method-assign]

        payload = client.health_live()

        self.assertEqual(payload["status"], "alive")
        self.assertEqual(calls, [("GET", "health/live", True)])
    def test_create_conversation_requires_csrf(self) -> None:
        client = NovoApiClient("http://localhost:8000")

        with self.assertRaisesRegex(RuntimeError, "Sign in"):
            client.create_conversation("Desktop test")


if __name__ == "__main__":
    unittest.main()