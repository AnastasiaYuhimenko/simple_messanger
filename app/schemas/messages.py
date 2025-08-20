from pydantic import BaseModel, Field
import datetime
from uuid import UUID


class Message(BaseModel):
    chat_id: UUID
    sender: str
    send_time: datetime.datetime = datetime.datetime.now()
    text: str


class MessageCreate(BaseModel):
    recipient_id: UUID = Field(..., description="ID получателя сообщения")
    content: str = Field(..., description="Содержимое сообщения")
