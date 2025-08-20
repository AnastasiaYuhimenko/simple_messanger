from fastapi import FastAPI, Request
from routers.users import router as users
from routers.chats import router as chats
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from exceptions import TokenExpiredException, TokenNoFoundException
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users, tags=["users"])
app.include_router(chats, tags=["chats"])

app.mount("/", StaticFiles(directory="frontend/static", html=True), name="static")
app.mount("/styles", StaticFiles(directory="frontend/static/styles"), name="styles")


@app.exception_handler(TokenExpiredException)
async def token_expired_exception_handler(request: Request, exc: HTTPException):
    # редирект на страницу /users/login
    return RedirectResponse(url="/users/login")


# Обработчик для ошибки TokenNoFound
@app.exception_handler(TokenNoFoundException)
async def token_no_found_exception_handler(request: Request, exc: HTTPException):
    # редирект на страницу /users/login
    return RedirectResponse(url="/users/login")
