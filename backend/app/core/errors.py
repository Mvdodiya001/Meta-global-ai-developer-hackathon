"""Typed backend errors (T1.2). Never swallow these; let callers handle them."""


class SourceUnavailable(Exception):
    """A source or source version cannot be found or loaded (F1)."""


class RuleCardError(Exception):
    """A rule card file is malformed or its span does not verify (T1.3, F2)."""


class LiveCallsBlocked(Exception):
    """A live model call was attempted where it is forbidden, e.g. under pytest (T2.1)."""


class CassetteMissing(Exception):
    """Replay mode found no cached response for a request hash (T2.1)."""


class LLMRequestFailed(Exception):
    """A live model request failed or its response did not parse (T2.1)."""
