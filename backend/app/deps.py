"""Auth dependencies for FastAPI routes."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import UserRole
from app.models import User
from app.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

_CREDS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise _CREDS_EXC
    try:
        payload = decode_token(creds.credentials)
    except JWTError:
        raise _CREDS_EXC

    user_id = payload.get("sub")
    if not user_id:
        raise _CREDS_EXC

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _CREDS_EXC
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return user


def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.admin.value, UserRole.editor.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor or admin privileges required",
        )
    return user