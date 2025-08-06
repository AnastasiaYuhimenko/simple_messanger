from pydantic import BaseModel


class Chat(BaseModel):
    users: list[str]
