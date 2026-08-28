from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.revocation import revoke
from app.core.security import (
    MAX_PASSWORD_BYTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: EmailStr
    # max_length is in CHARACTERS and bcrypt's limit is in BYTES, so this is a
    # cheap first gate; core.security enforces the real byte limit.
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    rider_id: int | None = None

    model_config = {"from_attributes": True}


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # One generic message for "no such user" AND "wrong password". Distinguishing
    # them turns the login endpoint into an account-enumeration oracle.
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user.email, is_admin=user.is_admin)
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    _: User = Depends(get_current_user),
):
    """Revoke the token presented on this request.

    Deliberately idempotent and silent: logging out twice, or with a token that
    already expired, is a 204 either way. There is nothing useful to tell a
    caller who is trying to end a session that is already over, and a
    distinguishable response would leak whether a token was live.

    Note this revokes ONE token, not the user. Logging out of a phone should not
    log you out of a laptop — that is what the per-token `jti` buys. Revoking
    every session for a user would mean a second denylist keyed on `sub` plus an
    issued-after timestamp, which is the natural next step but not this one.
    """
    if creds is not None:
        claims = decode_access_token(creds.credentials)
        if claims:
            revoke(claims.get("jti"), claims.get("exp"))
    return None
