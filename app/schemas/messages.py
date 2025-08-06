from pydantic import BaseModel
import datetime
from uuid import UUID


class Message(BaseModel):
    chat_id: UUID
    sender: str
    send_time: datetime.datetime = datetime.datetime.now()
    text: str
