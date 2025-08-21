from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlmodel import Session
from datetime import datetime, timedelta, timezone
import jwt
from db import get_session
from schemas.users import UserCreate, UserGet
from models.allmodels import User
from config import settings
from passlib.context import CryptContext
from schemas.token import TokenData
from fastapi import status
from sqlalchemy import select
from fastapi import Request


def get_user(user: UserGet, session: Session = Depends(get_session)):
    stmt = select(User).where(User.username == user.username)
    row = session.exec(stmt).first()
    if row is None:
        return None
    if isinstance(row, tuple) or hasattr(row, "_mapping"):
        return row[0]
    return row


def get_user_by_name(username: str, session: Session):
    stmt = select(User).where(User.username == username)
    result = session.exec(stmt).first()
    if result is None:
        return None
    if isinstance(result, tuple) or hasattr(result, "_mapping"):
        return result[0]
    return result


def get_user_by_id(userid: str, session: Session):
    stmt = select(User).where(User.id == userid)
    user = session.exec(stmt).first()
    if isinstance(user, tuple) or hasattr(user, "_mapping"):
        return user[0]
    return user


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def register_user(user_data: UserCreate, session: Session):
    user = User(**user_data.model_dump())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire, "token_type": "access_token"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


async def get_current_user(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("users_access_token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        userid = payload.get("sub")
        if userid is None:
            raise credentials_exception
        token_data = TokenData(user_id=userid)
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = get_user_by_id(userid=token_data.user_id, session=session)
    if user is None:
        raise credentials_exception

    return user


def create_refresh_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(days=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def get_current_user_refresh(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("refresh_token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        userid = payload.get("sub")
        if userid is None:
            raise credentials_exception
        token_data = TokenData(user_id=userid)
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = get_user_by_id(userid=token_data.user_id, session=session)
    if user is None:
        raise credentials_exception

    return userid
