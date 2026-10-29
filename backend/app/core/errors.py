"""Typed backend errors (T1.2). Never swallow these; let callers handle them."""


class SourceUnavailable(Exception):
    """A source or source version cannot be found or loaded (F1)."""
