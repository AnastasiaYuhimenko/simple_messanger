from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")


class Settings:
    POSTGRES_URL = os.getenv("POSTGRES_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


settings = Settings()
