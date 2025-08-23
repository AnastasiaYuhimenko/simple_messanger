from pydantic import BaseModel, Field
import datetime
from uuid import UUID


class Message(BaseModel):
    chat_id: UUID
    sender_id: str
    send_time: datetime.datetime = datetime.datetime.now()
    text: str


class MessageCreate(BaseModel):
    recipient_id: UUID = Field(..., description="ID получателя сообщения")
    content: str = Field(..., description="Содержимое сообщения")


class GroupMessagesCreate(BaseModel):
    chat_id: UUID
    text: str


class GroupMessageRead(BaseModel):
    chat_id: UUID
    text: str
    sender_id: UUID
    send_time: datetime.datetime
