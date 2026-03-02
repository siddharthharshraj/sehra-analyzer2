"""Authentication router: login and token refresh."""

import logging

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import create_access_token, decode_token
from api.core.db import get_session, User
from api.deps import get_current_user
from api.schemas import LoginRequest, TokenResponse, UserInfo, ChangePasswordRequest

logger = logging.getLogger("sehra.routers.auth")

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """Authenticate user with username/password and return JWT."""
    with get_session() as session:
        user = session.query(User).filter(User.username == body.username).first()
        if not user:
            logger.warning("Login failed: user '%s' not found", body.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        # Verify bcrypt password
        try:
            password_valid = bcrypt.checkpw(
                body.password.encode("utf-8"),
                user.password_hash.encode("utf-8"),
            )
        except Exception as e:
            logger.error("Password verification error for '%s': %s", body.username, e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        if not password_valid:
            logger.warning("Login failed: wrong password for '%s'", body.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        # Create JWT
        token = create_access_token({
            "sub": user.username,
            "name": user.name,
            "role": user.role,
        })

        logger.info("User '%s' logged in successfully", user.username)
        return TokenResponse(
            access_token=token,
            user=UserInfo(
                username=user.username,
                name=user.name,
                role=user.role,
            ),
        )


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change password for the authenticated user."""
    with get_session() as session:
        user = session.query(User).filter(User.username == current_user["sub"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # Verify current password
        try:
            valid = bcrypt.checkpw(
                body.current_password.encode("utf-8"),
                user.password_hash.encode("utf-8"),
            )
        except Exception:
            valid = False

        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        # Hash new password and update
        new_hash = bcrypt.hashpw(body.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password_hash = new_hash
        logger.info("Password changed for user '%s'", current_user["sub"])

    return {"detail": "Password changed successfully."}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh an existing valid token with a new expiration."""
    token = create_access_token({
        "sub": current_user["sub"],
        "name": current_user["name"],
        "role": current_user["role"],
    })

    logger.info("Token refreshed for user '%s'", current_user["sub"])
    return TokenResponse(
        access_token=token,
        user=UserInfo(
            username=current_user["sub"],
            name=current_user["name"],
            role=current_user["role"],
        ),
    )
