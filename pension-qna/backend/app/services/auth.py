from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, hash_token, new_refresh_token, verify_password
from app.db.models import RefreshToken, User
from app.schemas import RegisterRequest, TokenResponse


def public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name, "phone": user.phone}


def issue_tokens(session: Session, user: User) -> TokenResponse:
    raw_refresh = new_refresh_token()
    session.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=7),
    ))
    session.commit()
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=raw_refresh, user=public_user(user))


def register(session: Session, request: RegisterRequest) -> TokenResponse:
    if session.scalar(select(User).where(User.email == request.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 가입된 이메일입니다.")
    user = User(email=str(request.email), password_hash=hash_password(request.password), name=request.name, phone=request.phone)
    session.add(user)
    session.commit()
    session.refresh(user)
    return issue_tokens(session, user)


def login(session: Session, email: str, password: str) -> TokenResponse:
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return issue_tokens(session, user)


def rotate_refresh_token(session: Session, raw_token: str) -> TokenResponse:
    token = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    now = datetime.now(UTC).replace(tzinfo=None)
    if token is None or token.revoked_at is not None or token.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="리프레시 토큰이 유효하지 않습니다.")
    token.revoked_at = now
    session.commit()
    return issue_tokens(session, token.user)
