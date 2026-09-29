from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from backend.core.security import create_access_token
from backend.core.security import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.app.auth_schemas import AuthResponse
from backend.app.auth_schemas import LoginRequest
from backend.app.auth_schemas import RegisterRequest
from backend.app.auth_schemas import UserResponse
from backend.app.services.auth import authenticate_user
from backend.app.services.auth import create_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):

    try:

        user = create_user(
            db,
            request,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(
            user
        ),
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):

    user = authenticate_user(
        db,
        request.email,
        request.password,
    )

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(
            user
        ),
    )


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return UserResponse.model_validate(
        current_user
    )