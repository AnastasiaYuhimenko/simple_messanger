from uuid import UUID
from pydantic import BaseModel


class Chat(BaseModel):
    users: list[str]


class GroupChat(BaseModel):
    owner_id: UUID
    title: str
    members: list[str]


class GroupChatCreate(BaseModel):
    title: str
    members: list[str]


class GroupChatOut(BaseModel):
    title: str
    owner_id: UUID
    members: list
