from pydantic import BaseModel, EmailStr, field_validator, HttpUrl
from fastapi import HTTPException
import re


class User(BaseModel):
    img: HttpUrl
    username: str
    email: EmailStr
    hashed_password: str


class UserCreate(BaseModel):
    img: HttpUrl
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        if len(password) < 8:
            raise HTTPException(
                status_code=400, detail="Пароль должен содержать минимум 8 символов"
            )
        if not re.search(r"[A-Z]", password):
            raise HTTPException(
                status_code=400,
                detail="Пароль должен содержать хотя бы одну заглавную букву",
            )
        if not re.search(r"[a-z]", password):
            raise HTTPException(
                status_code=400,
                detail="Пароль должен содержать хотя бы одну строчную букву",
            )
        if not re.search(r"[0-9]", password):
            raise HTTPException(
                status_code=400, detail="Пароль должен содержать хотя бы одну цифру"
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(
                status_code=400,
                detail="Пароль должен содержать хотя бы один специальный символ",
            )
        return password


class UserOut(BaseModel):
    username: str
    email: EmailStr
    img: HttpUrl


class UserGet(BaseModel):
    username: str
    password: str
