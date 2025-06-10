# src/python_be/server/handlers/auth.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from ..models.models import User
from ..schemas.schemas import RegisterRequest, RegisterResponse

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_handler(
    req: RegisterRequest,
    db: Session,            # <-- now a SQLAlchemy Session, not a raw psycopg2 connection
) -> RegisterResponse:
    # 1) check if username already exists
    existing_user = db.query(User).filter(User.username == req.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # 2) hash password
    hashed = pwd_ctx.hash(req.password)

    # 3) create & persist the new user
    new_user = User(username=req.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4) return only the safe bits
    return RegisterResponse(id=new_user.id, username=new_user.username)
