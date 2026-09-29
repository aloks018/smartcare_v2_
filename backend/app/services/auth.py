from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.security import hash_password, verify_password
from backend.models.user import User


def create_user(db: Session, request) -> User:
    existing_user = db.scalar(
        select(User).where(User.email == str(request.email))
    )
    if existing_user is not None:
        raise ValueError("An account with this email already exists.")

    user = User(
        email=str(request.email),
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone=request.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user