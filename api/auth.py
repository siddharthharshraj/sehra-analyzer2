"""JWT token creation and verification using python-jose."""

import logging
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from api.config import get_settings

logger = logging.getLogger("sehra.auth")


def create_access_token(data: dict) -> str:
    """Create a JWT access token.

    Args:
        data: Dict containing at minimum 'sub' (username), 'name', and 'role'.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    logger.info("Created access token for user: %s", data.get("sub", "unknown"))
    return token


def decode_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded payload dict with 'sub', 'name', 'role', 'exp'.

    Raises:
        JWTError: If token is invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("Token decode failed: %s", e)
        raise
