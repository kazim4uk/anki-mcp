"""Thin HTTP client for the AnkiConnect add-on.

AnkiConnect exposes a JSON API on http://127.0.0.1:8765. Every request is
``{"action", "version": 6, "params"}`` and every response is
``{"result": ..., "error": ...}``. This module wraps that in a single
``invoke()`` helper and turns transport/API failures into a friendly
``AnkiError`` that the MCP tools can surface to the user.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_URL = "http://127.0.0.1:8765"
ANKICONNECT_VERSION = 6
ADDON_CODE = "2055492159"


class AnkiError(RuntimeError):
    """Raised when AnkiConnect is unreachable or an action fails."""


def _url() -> str:
    return os.environ.get("ANKI_CONNECT_URL", DEFAULT_URL) or DEFAULT_URL


def _timeout() -> float:
    try:
        return float(os.environ.get("ANKI_CONNECT_TIMEOUT", "15"))
    except ValueError:
        return 15.0


def invoke(action: str, **params: Any) -> Any:
    """Call an AnkiConnect ``action`` and return its ``result``.

    Raises :class:`AnkiError` with an actionable message when Anki Desktop or
    the AnkiConnect add-on is not available, or when the action itself fails.
    """
    payload: dict[str, Any] = {
        "action": action,
        "version": ANKICONNECT_VERSION,
        "params": params,
    }
    api_key = os.environ.get("ANKI_CONNECT_API_KEY")
    if api_key:
        payload["key"] = api_key

    try:
        response = httpx.post(_url(), json=payload, timeout=_timeout())
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise AnkiError(
            f"Cannot reach AnkiConnect at {_url()}. Make sure Anki Desktop is "
            f"running and the AnkiConnect add-on (code {ADDON_CODE}) is "
            "installed, then try again."
        ) from exc
    except httpx.TimeoutException as exc:
        raise AnkiError(
            f"AnkiConnect timed out after {_timeout():.0f}s at {_url()}. "
            "Is Anki busy or waiting on a dialog?"
        ) from exc
    except httpx.HTTPError as exc:
        raise AnkiError(f"AnkiConnect HTTP error: {exc}") from exc

    data = response.json()
    if not isinstance(data, dict) or "error" not in data or "result" not in data:
        raise AnkiError(f"Unexpected AnkiConnect response: {data!r}")
    if data["error"] is not None:
        raise AnkiError(f"AnkiConnect error: {data['error']}")
    return data["result"]
