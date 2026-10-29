"""Typed backend errors (T1.2). Never swallow these; let callers handle them."""


class SourceUnavailable(Exception):
    """A source or source version cannot be found or loaded (F1)."""


class RuleCardError(Exception):
    """A rule card file is malformed or its span does not verify (T1.3, F2)."""
