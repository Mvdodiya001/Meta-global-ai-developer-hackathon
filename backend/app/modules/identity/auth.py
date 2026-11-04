"""Sign-in: password accounts and HMAC session tokens (Identity).

Passwords are PBKDF2-HMAC-SHA256 with a per-user salt (stdlib only).
Tokens are compact HMAC-SHA256 signed payloads (JWT-shaped) with the
secret from `CT_AUTH_SECRET` (a development default is used when unset
— set it in any real deployment). Verification is constant-time.
Auth *enforcement* is opt-in per deployment (`CT_AUTH_REQUIRED=1`);
accounts and sign-in work either way, so the demo path is unchanged.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import models

TOKEN_TTL_SECONDS = 7 * 24 * 3600
_PBKDF2_ROUNDS = 120_000


class AuthError(Exception):
    """Registration or sign-in failed (Identity)."""


def _utcnow() -> str:
    """Current UTC time in ISO-8601 (Identity)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    """One prefixed random id (Identity)."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def hash_password(password: str) -> str:
    """Salted PBKDF2 hash in `pbkdf2$rounds$salt$hash` form."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2${_PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    """Constant-time password verification."""
    try:
        _kind, rounds, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def register_user(
    session: Session, *, email: str, password: str, name: str, tenant_id: str = "demo"
) -> models.User:
    """Create one account; duplicate emails are rejected."""
    email = email.strip().lower()
    if "@" not in email or len(password) < 8:
        raise AuthError("email must contain @ and password needs 8+ characters")
    existing = session.execute(
        sa.select(models.User).where(models.User.email == email)
    ).scalars().first()
    if existing is not None:
        raise AuthError("an account with this email already exists")
    if session.get(models.Tenant, tenant_id) is None:
        session.add(models.Tenant(id=tenant_id, name="Demo"))
    user = models.User(
        id=_new_id("U"),
        tenant_id=tenant_id,
        email=email,
        name=name.strip() or email,
        password_hash=hash_password(password),
        role="lawyer",
        created_at=_utcnow(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.expunge(user)
    return user


def authenticate(session: Session, *, email: str, password: str) -> models.User:
    """Verify credentials; one generic error for both failure modes."""
    user = session.execute(
        sa.select(models.User).where(models.User.email == email.strip().lower())
    ).scalars().first()
    if user is None or not check_password(password, str(user.password_hash)):
        raise AuthError("email or password is incorrect")
    session.expunge(user)
    return user


def _secret() -> bytes:
    """Token signing secret (set CT_AUTH_SECRET outside local dev)."""
    return os.environ.get("CT_AUTH_SECRET", "clausetrace-dev-secret").encode()


def _b64(data: bytes) -> str:
    """URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def issue_token(user: models.User) -> str:
    """Sign a session token for one user (7-day expiry)."""
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64(
        json.dumps(
            {
                "sub": str(user.id),
                "email": str(user.email),
                "tenant_id": str(user.tenant_id),
                "exp": int(time.time()) + TOKEN_TTL_SECONDS,
            }
        ).encode()
    )
    signature = _b64(
        hmac.new(_secret(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def decode_token(token: str) -> dict | None:
    """Verify signature + expiry; return the payload or None."""
    try:
        header, payload, signature = token.split(".")
        expected = _b64(
            hmac.new(_secret(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        return dict(data)
    except (ValueError, TypeError, KeyError):
        return None


def verify_token(session: Session, token: str) -> models.User | None:
    """Resolve a token to its user, or None when invalid/expired."""
    data = decode_token(token)
    if data is None:
        return None
    user = session.get(models.User, str(data.get("sub")))
    if user is not None:
        session.expunge(user)
    return user


def auth_required() -> bool:
    """Whether this deployment enforces sign-in on the API."""
    return os.environ.get("CT_AUTH_REQUIRED", "0") == "1"
