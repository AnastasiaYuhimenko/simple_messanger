from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from schemas.users import UserCreate, UserOut, UserGet
from passlib.context import CryptContext
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlmodel import Session, select
from db import get_session
from models.allmodels import User
from services.users import (
    create_refresh_token,
    get_current_user_refresh,
    get_user_by_id,
    register_user,
    create_access_token,
    get_user,
    get_current_user,
)
from schemas.token import Token
from fastapi import status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


router = APIRouter(prefix="/users")

templates = Jinja2Templates(directory="frontend/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


@router.get("/", response_class=HTMLResponse, summary="Страница авторизации")
async def get_categories(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, session: Session = Depends(get_session)):
    # проверки на то, что пользователь еще не зарегистрирован
    user_excec = get_user(user=user, session=session)
    if user_excec is not None:
        raise HTTPException(
            status_code=400, detail="Пользователь с данным username уже зарегистрирован"
        )
    statement = select(User).where(User.email == user.email)
    result = session.exec(statement).first()

    if result is not None:
        raise HTTPException(
            status_code=400, detail="Пользователь с данным email уже зарегистрирован"
        )

    # сама регистрация пользователя

    hashed = get_password_hash(user.password)

    user_db = User(username=user.username, email=user.email, hashed_password=hashed)

    return register_user(user_db, session)


@router.post("/login")
async def login(
    user: UserGet, response: Response, session: Session = Depends(get_session)
):
    user_obj = get_user(user=user, session=session)
    if user_obj is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный username или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(
        plain_password=user.password, hashed_password=user_obj.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный username или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user_obj.id)})
    refresh_token = create_refresh_token(
        data={"sub": str(user_obj.id), "token_type": "refresh_token"}
    )
    response.set_cookie(
        key="users_access_token", path="/", value=access_token, httponly=True
    )
    response.set_cookie(key="refresh_token", path="/", value=refresh_token)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/user/me", response_model=UserOut)
async def get_me(current_user: Annotated[UserOut, Depends(get_current_user)]):
    return current_user


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token", path="/")
    return {"message": "Пользователь успешно вышел из системы"}


@router.post("/refresh")
def refresh(
    response: Response,
    user_id: Annotated[UserOut, Depends(get_current_user_refresh)],
    request: Request,
):
    access_token = create_access_token(data={"sub": str(user_id)})
    response.set_cookie(
        key="users_access_token", path="/", value=access_token, httponly=True
    )
    return Token(
        access_token=access_token, refresh_token=request.cookies.get("refresh_token")
    )
