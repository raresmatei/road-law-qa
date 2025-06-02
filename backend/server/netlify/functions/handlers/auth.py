# src/python_be/server/handlers/auth.py

from fastapi import HTTPException, status
from passlib.context import CryptContext
from ..schemas.schemas import RegisterRequest, RegisterResponse

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def register_handler(
    req: RegisterRequest,
    db_conn,            # this is your psycopg2.Connection
) -> RegisterResponse:
    cursor = db_conn.cursor()
    try:
        # 1) see if that username already exists
        cursor.execute(
            "SELECT id FROM users WHERE username = %s",
            (req.username,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # 2) hash the incoming password
        hashed = pwd_ctx.hash(req.password)

        # 3) create & persist the new user
        cursor.execute(
            """
            INSERT INTO users (username, hashed_password)
            VALUES (%s, %s)
            RETURNING id
            """,
            (req.username, hashed)
        )
        user_id = cursor.fetchone()[0]
        db_conn.commit()

    except HTTPException:
        # re-raise your own HTTP errors
        db_conn.rollback()
        raise

    except Exception as e:
        db_conn.rollback()
        print('error: ', e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error creating user"
        ) from e

    finally:
        cursor.close()

    # 4) return just the safe bits
    return RegisterResponse(id=user_id, username=req.username)
