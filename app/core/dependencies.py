"""Auth dependencies — who is calling, and may they."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# auto_error=False so a missing header produces our 401 envelope rather than
# FastAPI's default shape — one error contract across the whole API.
_bearer = HTTPBearer(auto_error=False)

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _UNAUTHENTICATED

    claims = decode_access_token(creds.credentials)
    if claims is None or not claims.get("sub"):
        raise _UNAUTHENTICATED

    # Load the user rather than trusting the token's claims wholesale: a token
    # stays valid until it expires, so a user deleted or demoted a minute ago
    # would otherwise keep full access for the rest of the token's life.
    user = db.query(User).filter(User.email == claims["sub"]).first()
    if user is None:
        raise _UNAUTHENTICATED
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """403, not 401: the caller IS authenticated, they're just not allowed."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
