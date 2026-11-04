"""Phase 6: upload safety — size limits and a malware-scan hook.

Size limits are enforced on decoded bytes before any parsing. The scan
hook is intentionally small: it rejects known-bad test signatures
(EICAR) and is the single seam where a real AV engine (e.g. ClamAV via
`CT_MALWARE_SCANNER=clamav`) gets plugged in; unknown scanners fail
closed at startup of the check, never silently pass.
"""

import os

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # documents
MAX_MEDIA_BYTES = 10 * 1024 * 1024  # scans + dictation audio

_EICAR = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"


class UploadRejected(Exception):
    """Typed upload refusal (Phase 6)."""


def check_size(data: bytes, *, limit: int = MAX_UPLOAD_BYTES, what: str = "file") -> None:
    """Reject oversize payloads before parsing (Phase 6)."""
    if len(data) > limit:
        raise UploadRejected(f"{what} is larger than {limit // (1024 * 1024)} MB")


def scan_bytes(data: bytes) -> None:
    """Malware-scan hook: reject known-bad content (Phase 6).

    Default scanner catches the EICAR test signature (the industry
    canary). `CT_MALWARE_SCANNER` names the engine; anything other
    than the built-in `signature` engine is rejected loudly here so a
    misconfigured deployment fails closed instead of scanning nothing.
    """
    engine = os.environ.get("CT_MALWARE_SCANNER", "signature").lower()
    if engine != "signature":
        raise UploadRejected(f"malware scanner {engine!r} is not configured on this server")
    if _EICAR in data:
        raise UploadRejected("file failed the malware scan")


def check_upload(data: bytes, *, limit: int = MAX_UPLOAD_BYTES, what: str = "file") -> None:
    """Size + scan gate applied to every uploaded payload (Phase 6)."""
    check_size(data, limit=limit, what=what)
    scan_bytes(data)
