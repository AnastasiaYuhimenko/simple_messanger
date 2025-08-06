from fastapi import FastAPI
from routers.users import router as users
from routers.chats import router as chats
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


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

app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    return {"message": "Hello World"}
