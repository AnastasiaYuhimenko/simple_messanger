from fastapi import status, HTTPException


class TokenExpiredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек")


class TokenNoFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не найден"
        )


NoJwtException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не валидный!"
)

NoUserIdException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Не найден ID пользователя"
)

ForbiddenException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав!"
)
