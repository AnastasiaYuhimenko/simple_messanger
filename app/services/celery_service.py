from uuid import UUID
from sqlmodel import insert
from models.allmodels import Message, GroupMessage
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


@celery_app.task
def send_message_later_group(message_data: dict):
    recipients_uuid = [UUID(r) for r in message_data["recipients"]]
    stmt = insert(GroupMessage).values(
        group_id=message_data["group_id"],
        sender=message_data["sender"],
        recipients=recipients_uuid,
        text=message_data["text"],
    )

    with engine.begin() as conn:
        conn.execute(stmt)

    return {
        "group_id": message_data["group_id"],
        "recipients": message_data["recipients"],
        "text": message_data["text"],
        "status": "ok",
        "msg": "Message saved!",
    }
