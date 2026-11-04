"""In-process domain events between modules (Rewrite P2).

Modules publish facts about what they did (`finding.decided`,
`fact.approved`, `impact.applied`, …); other modules may subscribe
without importing the publisher. Synchronous and explicit: a failing
handler propagates, because a silently dropped side effect is worse
than a loud error. The async/queued transport replaces this bus
behind the same subscribe/emit surface in P3+.

This bus carries notifications only. It never decides a finding
status — that remains the verification memory service alone.
"""

from collections.abc import Callable
from typing import Any

Handler = Callable[[dict[str, Any]], None]

_handlers: dict[str, list[Handler]] = {}


def subscribe(event: str, handler: Handler) -> None:
    """Register one handler for an event name (P2)."""
    _handlers.setdefault(event, []).append(handler)


def unsubscribe(event: str, handler: Handler) -> None:
    """Remove one handler (mainly for tests) (P2)."""
    handlers = _handlers.get(event, [])
    if handler in handlers:
        handlers.remove(handler)


def clear() -> None:
    """Drop all handlers (tests) (P2)."""
    _handlers.clear()


def emit(event: str, payload: dict[str, Any]) -> None:
    """Deliver one event to its handlers, in subscription order (P2)."""
    for handler in list(_handlers.get(event, [])):
        handler(payload)
