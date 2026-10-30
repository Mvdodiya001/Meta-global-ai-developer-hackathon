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


class ExtractionError(Exception):
    """Model output is not a valid clause extraction (T2.2, F3)."""


class ClaimError(Exception):
    """A question cannot be typed as a closed claim (T2.3, F4)."""


class MemoryServiceError(Exception):
    """The memory service cannot decide a claim as asked (T3.3, F7)."""


class ChallengerError(Exception):
    """A challenger review failed or is misconfigured (T6.1, F17)."""


class ToolError(Exception):
    """A tool call was rejected or failed validation (T2.4, F5)."""

    def __init__(self, message: str, code: str = "tool_rejected") -> None:
        """Keep the machine-readable code next to the message (T2.4)."""
        super().__init__(message)
        self.code = code
