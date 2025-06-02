# src/python_be/server/handlers/login.py

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
import psycopg2

from ..schemas.schemas import LoginRequest, LoginResponse
from ...utils.settings import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def login_handler(
    req: LoginRequest,
    conn: psycopg2.extensions.connection
) -> LoginResponse:
    # 1) open a cursor and look up the user by username
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, hashed_password
          FROM users
         WHERE username = %s
        """,
        (req.username,)
    )
    row = cur.fetchone()
    cur.close()

    # 2) verify we found a user and the password matches
    if not row or not pwd_ctx.verify(req.password, row[1]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = row[0]

    # 3) issue JWT
    token = jwt.encode(
        {"sub": str(user_id)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )

    return LoginResponse(access_token=token, token_type="bearer")
