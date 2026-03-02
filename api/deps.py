"""FastAPI dependencies for authentication and authorization."""

import logging

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError

from api.auth import decode_token

logger = logging.getLogger("sehra.deps")


def get_current_user(authorization: str = Header(...)) -> dict:
    """Extract and validate Bearer token from Authorization header.

    Returns:
        Dict with 'sub' (username), 'name', and 'role'.

    Raises:
        HTTPException 401: If token is missing, malformed, or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Strip "Bearer "
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub' claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "sub": username,
        "name": payload.get("name", username),
        "role": payload.get("role", "analyst"),
    }


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Ensure the current user has admin role.

    Returns:
        The user dict if authorized.

    Raises:
        HTTPException 403: If user is not an admin.
    """
    if user.get("role") != "admin":
        logger.warning(
            "Non-admin user '%s' attempted admin action", user.get("sub")
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user
