import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

JWT_SECRET = os.getenv("JWT_SECRET", "local-development-secret")
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return "pbkdf2_sha256$600000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, rounds, encoded_salt, encoded_digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(encoded_salt), int(rounds)
        )
        return secrets.compare_digest(digest, base64.b64decode(encoded_digest))
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: int) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=30)
    header = _encode_segment({"alg": JWT_ALGORITHM, "typ": "JWT"})
    payload = _encode_segment({"sub": str(user_id), "exp": int(expires.timestamp())})
    signature = _sign(f"{header}.{payload}")
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> int:
    try:
        header, encoded_payload, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(f"{header}.{encoded_payload}")):
            raise ValueError("invalid signature")
        payload = _decode_segment(encoded_payload)
        if payload["exp"] <= int(datetime.now(UTC).timestamp()):
            raise ValueError("expired")
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 정보가 유효하지 않습니다.") from exc


def _encode_segment(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _decode_segment(value: str) -> dict:
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _sign(value: str) -> str:
    digest = hmac.new(JWT_SECRET.encode(), value.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
