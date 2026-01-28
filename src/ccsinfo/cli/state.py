"""Global CLI state."""

from __future__ import annotations


class State:
    """Global state for CLI options."""

    server_url: str | None = None


state = State()
