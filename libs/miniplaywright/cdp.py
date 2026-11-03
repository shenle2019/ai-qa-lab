"""Minimal Chrome DevTools Protocol client over WebSocket."""

from __future__ import annotations

import json
from typing import Any

from websockets.sync.client import connect

from .errors import CDPError


class CDPConnection:
    def __init__(self, ws_url: str) -> None:
        self.ws = connect(ws_url, max_size=None, open_timeout=15, legacy=True)
        self._next_id = 0

    def send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._next_id += 1
        message_id = self._next_id
        payload = {"id": message_id, "method": method, "params": params or {}}
        try:
            self.ws.send(json.dumps(payload))
            while True:
                raw = self.ws.recv(timeout=30)
                message = json.loads(raw)
                if message.get("id") != message_id:
                    continue
                if "error" in message:
                    raise CDPError(f"{method}: {message['error']}")
                return message.get("result", {})
        except CDPError:
            raise
        except Exception as exc:
            raise CDPError(f"{method} failed: {exc}") from exc

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass
