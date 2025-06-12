# src/python_be/server/handlers/login.py

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models.models import User
from ..schemas.schemas import LoginRequest, LoginResponse
from ...utils.settings import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def login_handler(
    req: LoginRequest,
    db: Session,
) -> LoginResponse:
    # 1) look up the user by username
    user = db.query(User).filter(User.username == req.username).first()

    # 2) verify user exists and password matches
    if not user or not pwd_ctx.verify(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3) check admin credentials
    #    we compare the incoming creds against your configured admin
    is_admin = False
    if req.username == settings.ADMIN_USERNAME:
        # only verify password against the ADMIN_PASSWORD_HASH
        if pwd_ctx.verify(req.password, settings.ADMIN_PASSWORD_HASH):
            is_admin = True

    # 4) issue JWT with an extra "admin" claim
    payload = {
        "sub": str(user.id),
        "admin": is_admin,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    # 5) return token + flag
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        is_admin=is_admin,
    )
