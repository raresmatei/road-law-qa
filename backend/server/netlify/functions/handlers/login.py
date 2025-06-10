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
    db: Session,  # now a SQLAlchemy Session
) -> LoginResponse:
    # 1) look up the user by username via SQLAlchemy
    user = db.query(User).filter(User.username == req.username).first()

    # 2) verify we found a user and the password matches
    if not user or not pwd_ctx.verify(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3) issue JWT
    token = jwt.encode(
        {"sub": str(user.id)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )

    return LoginResponse(access_token=token, token_type="bearer")
