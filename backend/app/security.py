from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.models import User

password_hash = PasswordHash.recommended()
# Perform a password hash check even when an email is unknown.
dummy_hash = password_hash.hash("not-a-real-account-password")
bearer = HTTPBearer(auto_error=False)


def get_session(request: Request):
    with request.app.state.session_factory() as session:
        yield session


def unauthorized():
    return HTTPException(401, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.", headers={"WWW-Authenticate": "Bearer"})


def issue_token(user: User, config):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=config.access_token_minutes), "iss": "private-ai", "aud": "private-ai-web"},
        config.jwt_secret.get_secret_value(), algorithm="HS256",
    )


def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer), session: Session = Depends(get_session)):
    if credentials is None:
        raise unauthorized()
    try:
        payload = jwt.decode(credentials.credentials, request.app.state.settings.jwt_secret.get_secret_value(), algorithms=["HS256"], audience="private-ai-web", issuer="private-ai", options={"require": ["sub", "iat", "exp", "iss", "aud"]})
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized()
    user = session.get(User, user_id)
    if user is None:
        raise unauthorized()
    return user
