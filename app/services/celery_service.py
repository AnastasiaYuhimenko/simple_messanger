from sqlmodel import insert
from models.allmodels import Message
from db import engine
from celery_app import celery_app


@celery_app.task
def send_message_later(message_data: dict):
    stmt = insert(Message).values(
        sender=message_data["sender_id"],
        user2=message_data["recipient_id"],
        text=message_data["content"],
    )

    with engine.begin() as conn:
        conn.execute(stmt)

    return {
        "recipient_id": message_data["recipient_id"],
        "content": message_data["content"],
        "status": "ok",
        "msg": "Message saved!",
    }
