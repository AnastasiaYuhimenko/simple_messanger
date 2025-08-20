import asyncio
from uuid import UUID
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from typing import Annotated, Dict, List
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from db import get_session
from models.allmodels import User, Chat
from schemas.users import UserOut
from schemas.messages import MessageCreate, Message
from services.users import get_current_user, get_user_by_name
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, any_, or_
from models.allmodels import Message as ModelMessage


router = APIRouter()


# Активные WebSocket-подключения: {user_id: websocket}
active_connections: Dict[int, WebSocket] = {}


# Функция для отправки сообщения пользователю, если он подключен
async def notify_user(user_id: UUID, message: dict):
    user_id = str(user_id)
    """Отправить сообщение пользователю, если он подключен."""
    if user_id in active_connections:
        websocket = active_connections[user_id]
        # Отправляем сообщение в формате JSON
        await websocket.send_json(message)


# WebSocket эндпоинт для соединений
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    # Принимаем WebSocket-соединение
    await websocket.accept()
    # Сохраняем активное соединение для пользователя
    active_connections[user_id] = websocket
    try:
        while True:
            # Просто поддерживаем соединение активным (1 секунда паузы)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Удаляем пользователя из активных соединений при отключении
        active_connections.pop(user_id, None)


@router.post("/create_chat")
async def create_chat(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    user2_username: str = Body(..., embed=True),
    session: Session = Depends(get_session),
):
    user1 = session.get(User, current_user.id)
    user2 = get_user_by_name(username=user2_username, session=session)

    if user2 is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    users_list = sorted([user1.id, user2.id])

    stmt = select(Chat).where(Chat.users == users_list)
    existing_chat = session.exec(stmt).first()
    if existing_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Чат с такими пользователями уже существует",
        )

    chat_db = Chat(users=users_list)
    session.add(chat_db)
    session.commit()
    session.refresh(chat_db)
    return chat_db


templates = Jinja2Templates(directory="frontend/templates")


@router.get("/chat", response_class=HTMLResponse, summary="Chat Page")
async def get_chat_page(
    request: Request,
    user_data: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = select(Chat).where(user_data.id == any_(Chat.users))
    result = session.exec(query)
    chats = result.all()

    users_list = []
    unique_users = {}
    for chat in chats:
        if chat.users == [user_data.id, user_data.id]:
            unique_users[user_data.id] = user_data
        for user_id in chat.users:
            if user_id != user_data.id:
                user = session.get(User, user_id)
                if user:
                    unique_users[user.id] = user

    users_list = list(unique_users.values())

    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "user": user_data, "users_all": users_list},
    )


@router.get("/messages/{user_id}", response_model=List[Message])
async def get_messages(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = select(ModelMessage).where(
        or_(
            and_(user_id == ModelMessage.sender, current_user.id == ModelMessage.user2),
            and_(user_id == ModelMessage.user2, current_user.id == ModelMessage.sender),
        )
    )
    result = session.exec(query)
    messages = result.all()
    messages_out = [
        {
            "chat_id": str(
                message.id
            ),  # если chat_id нет, можно использовать id сообщения
            "sender": str(message.sender),  # UUID → строка
            "text": message.text,
            "send_time": message.send_time.isoformat(),  # datetime → строка
            "recipient_id": str(message.user2),  # если у Pydantic есть такое поле
        }
        for message in messages
    ]

    return messages_out


# добавление сообщений
@router.post("/messages", response_model=MessageCreate)
async def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    db_message = ModelMessage(
        user2=message.recipient_id, text=message.content, sender=current_user.id
    )
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    message_data = {
        "sender_id": current_user.id,
        "recipient_id": message.recipient_id,
        "content": message.content,
    }
    # Уведомляем получателя и отправителя через WebSocket
    await notify_user(message.recipient_id, message_data)
    await notify_user(current_user.id, message_data)

    return {
        "recipient_id": message.recipient_id,
        "content": message.content,
        "status": "ok",
        "msg": "Message saved!",
    }


@router.get(
    "/create_chat_page", response_class=HTMLResponse, summary="Create Chat Page"
)
async def get_create_chat_page(
    request: Request, user_data: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "create_chat.html", {"request": request, "user": user_data}
    )
