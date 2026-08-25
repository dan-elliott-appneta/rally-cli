"""Adapter that exposes a synchronous Rally client through an async interface."""

from __future__ import annotations

import inspect
from typing import Any


def as_async_client(client: Any) -> Any:
    """Return an async-interfaced view of a client, wrapping it if it's sync."""
    if inspect.iscoroutinefunction(getattr(client, "get_tickets", None)):
        return client
    return AsyncClientAdapter(client)


class AsyncClientAdapter:
    """Wraps a synchronous client so its methods can be awaited.

    The TUI talks to a single async client interface. AsyncRallyClient already
    fits it; MockRallyClient is synchronous and in-memory, so awaiting it costs
    nothing. This adapter bridges the two rather than duplicating every mock
    method as ``async def``.

    Properties (workspace, project, current_user, current_iteration) pass
    through unchanged; callables are wrapped in a coroutine.
    """

    def __init__(self, client: Any) -> None:
        """Wrap a synchronous Rally client.

        Args:
            client: The synchronous client to adapt.
        """
        self._client = client

    @property
    def wrapped(self) -> Any:
        """The underlying synchronous client."""
        return self._client

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        async def call(*args: Any, **kwargs: Any) -> Any:
            return attr(*args, **kwargs)

        return call
