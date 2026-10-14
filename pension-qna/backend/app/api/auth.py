from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth import login, register, rotate_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_route(request: RegisterRequest, session: Session = Depends(get_db)) -> TokenResponse:
    return register(session, request)


@router.post("/login", response_model=TokenResponse)
def login_route(request: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    return login(session, str(request.email), request.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh_route(request: RefreshRequest, session: Session = Depends(get_db)) -> TokenResponse:
    return rotate_refresh_token(session, request.refresh_token)
