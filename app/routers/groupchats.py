import asyncio
from datetime import datetime, timedelta
import logging
from typing import Annotated, Dict, List
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi import Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, select
from sqlmodel import Session

from db import get_session
from schemas.messages import GroupMessagesCreate, GroupMessageRead
from schemas.users import UserOut
from services.celery_service import send_message_later_group
from services.users import get_current_user, get_user_by_id, get_user_by_name
from schemas.chats import GroupChatCreate, GroupChatOut, GroupChat
from models.allmodels import GroupChatMembers, GroupMessage, Role, User

router = APIRouter(prefix="/group_chats")
templates = Jinja2Templates(directory="frontend/templates")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_chat_members(
    chat_id: str,
    current_user: UserOut,
    session: Session,
):
    chat = session.exec(select(GroupChat).where(GroupChat.id == chat_id)).scalar()
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    cur_user_in_chat = session.exec(
        select(GroupChatMembers).where(
            and_(GroupChatMembers.user_id == current_user.id),
            (GroupChatMembers.group_id == chat_id),
        )
    ).scalar_one_or_none()
    if cur_user_in_chat is None:
        raise HTTPException(status_code=422, detail="Вы не состоите в данном чате")

    members = session.exec(
        select(GroupChatMembers).where(GroupChatMembers.group_id == chat_id)
    ).scalars()

    members = [
        get_user_by_id(member.user_id, session=session).username for member in members
    ]
    return members


active_connections: Dict[int, WebSocket] = {}


async def notify_user(user_id: UUID, message: dict):
    user_id = str(user_id)
    if user_id in active_connections:
        websocket = active_connections[user_id]
        await websocket.send_json(message)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)


@router.post("/create", response_model=GroupChatOut)
def create_chat(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    chat: GroupChatCreate,
    session: Session = Depends(get_session),
):
    members_list = [
        get_user_by_name(user, session=session) for user in list(set(chat.members))
    ]
    if None in members_list:
        raise HTTPException(
            status_code=404, detail="Пользователь из списка участников группы не найден"
        )
    members_list = sorted([member.id for member in members_list])
    current_user = get_user_by_name(current_user.username, session=session).id
    members_list.append(current_user)
    chat_db = GroupChat(title=chat.title, owner_id=current_user)
    session.add(chat_db)
    session.commit()
    session.refresh(chat_db)
    for member in members_list:
        if member != current_user:
            member_db = GroupChatMembers(group_id=chat_db.id, user_id=member)
        else:
            member_db = GroupChatMembers(
                group_id=chat_db.id, user_id=member, role=Role.owner
            )
        session.add(member_db)
        session.commit()

    return GroupChatOut(owner_id=current_user, title=chat.title, members=members_list)


@router.post("/add_member")
def add_member(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    session: Session = Depends(get_session),
    chat_id: str = Body(..., embed=True),
    new_user: str = Body(..., embed=True),
):
    chat = session.exec(select(GroupChat).where(GroupChat.id == chat_id)).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if current_user is None:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")
    cur_user_in_chat = session.exec(
        select(GroupChatMembers).where(
            and_(GroupChatMembers.user_id == current_user.id),
            (GroupChatMembers.group_id == chat_id),
        )
    ).first()
    if cur_user_in_chat is None:
        raise HTTPException(status_code=422, detail="Вы не состоите в данном чате")
    new_user = get_user_by_name(new_user, session=session)
    if new_user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователя, которого вы хотите добавить не существует",
        )
    exists = session.exec(
        select(GroupChatMembers).where(
            and_(
                GroupChatMembers.user_id == new_user.id,
                GroupChatMembers.group_id == chat_id,
            )
        )
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Пользователь уже в чате")
    member = GroupChatMembers(group_id=chat_id, user_id=new_user.id, role=Role.member)
    session.add(member)
    session.commit()

    return {"status_code": "200 ok", "detail": "Пользователь добавлен"}


@router.delete("/delete_member")
def delete_member(
    chat_id: str = Body(..., embed=True),
    current_user: UserOut = Depends(get_current_user),
    member_name: str = Body(..., embed=True),
    session: Session = Depends(get_session),
):
    chat = session.exec(select(GroupChat).where(GroupChat.id == chat_id)).first()

    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if current_user is None:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")
    cur_user_in_chat = session.exec(
        select(GroupChatMembers).where(
            and_(GroupChatMembers.user_id == current_user.id),
            (GroupChatMembers.group_id == chat_id),
        )
    ).scalar_one_or_none()
    if cur_user_in_chat is None:
        raise HTTPException(status_code=422, detail="Вы не состоите в данном чате")
    if cur_user_in_chat.role not in (Role.admin, Role.owner):
        raise HTTPException(status_code=403, detail="Недостаточно првв")
    del_user = get_user_by_name(member_name, session=session)
    if del_user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователя, которого вы хотите удалить не существует",
        )
    exists = session.exec(
        select(GroupChatMembers).where(
            and_(
                GroupChatMembers.user_id == del_user.id,
                GroupChatMembers.group_id == chat_id,
            )
        )
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(
            status_code=409,
            detail="Пользователя, которого вы хотите удалить, нет в чате",
        )

    session.delete(exists)
    session.commit()

    return {"status_code": "200 ok", "detail": "Пользователь удален"}


@router.delete("/exit")
def exit(
    chat_id: str = Body(..., embed=True),
    current_user: UserOut = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    chat = session.exec(select(GroupChat).where(GroupChat.id == chat_id)).first()

    if chat is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if current_user is None:
        raise HTTPException(status_code=401, detail="Вы не авторизованы")
    cur_user_in_chat = session.exec(
        select(GroupChatMembers).where(
            and_(GroupChatMembers.user_id == current_user.id),
            (GroupChatMembers.group_id == chat_id),
        )
    ).scalar_one_or_none()
    if cur_user_in_chat is None:
        raise HTTPException(status_code=422, detail="Вы не состоите в данном чате")

    session.delete(cur_user_in_chat)
    session.commit()

    return {"status_code": "200 ok", "detail": "Вы вышли из чата"}


@router.post("/group_members")
def get_members(
    chat_id: str = Body(..., embed=True),
    current_user: UserOut = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_chat_members(chat_id=chat_id, current_user=current_user, session=session)


@router.post("/messages", response_model=GroupMessagesCreate)
async def send_message(
    message: GroupMessagesCreate,
    current_user: UserOut = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    recipients = [
        get_user_by_name(rec, session=session).id
        for rec in get_chat_members(
            chat_id=message.chat_id, current_user=current_user, session=session
        )
    ]
    db_message = GroupMessage(
        group_id=message.chat_id,
        recipients=recipients,
        text=message.text,
        sender=current_user.id,
    )
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    message_data = {
        "sender_id": current_user.id,
        "chat_id": message.chat_id,
        "text": message.text,
    }
    for user in recipients:
        await notify_user(user, message_data)
    await notify_user(current_user.id, message_data)

    return {
        "chat_id": message.chat_id,
        "text": message.text,
        "status": "ok",
        "msg": "Message saved!",
    }


@router.post("/messages_late")
def send_message_late(
    message: GroupMessagesCreate,
    time: int = Body(..., embed=True),
    current_user: UserOut = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    eta_time = datetime.utcnow() + timedelta(minutes=time)
    recipients = [
        str(get_user_by_name(rec, session=session).id)
        for rec in get_chat_members(
            chat_id=message.chat_id, current_user=current_user, session=session
        )
    ]
    message_data = {
        "sender": current_user.id,
        "recipients": recipients,
        "text": message.text,
        "group_id": message.chat_id,
    }

    send_message_later_group.apply_async(args=[message_data], eta=eta_time)
    return {"status": "scheduled", "send_time": eta_time}


@router.get("/chat", response_class=HTMLResponse, summary="Chat Page")
async def get_chat_page(
    request: Request,
    user_data: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = select(GroupChatMembers).where(GroupChatMembers.user_id == user_data.id)
    result = session.exec(query)
    memberships = result.scalars()

    group_ids = [m.group_id for m in memberships]
    chats = []
    if group_ids:
        chats = session.exec(
            select(GroupChat).where(GroupChat.id.in_(group_ids))
        ).scalars()
    chats_dicts = [{"id": str(chat.id), "title": chat.title} for chat in chats]
    return templates.TemplateResponse(
        "group_chat.html",
        {
            "request": request,
            "user": user_data,
            "user_id": str(user_data.id),
            "group_chats": chats_dicts,
            "username": user_data.username,
        },
    )


@router.get("/messages/{group_id}", response_model=List[GroupMessageRead])
async def get_messages(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    query = select(GroupMessage).where(GroupMessage.group_id == group_id)
    result = session.exec(query)
    messages = result.scalars()
    messages_out = [
        {
            "chat_id": str(message.group_id),
            "sender_id": str(message.sender),
            "text": message.text,
            "send_time": message.send_time.isoformat(),
            "recipients": message.recipients,
        }
        for message in messages
    ]

    return messages_out


@router.post("/group_owner")
def get_members_with_owner(
    chat_id: str = Body(..., embed=True),
    current_user: UserOut = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    owner_id = (
        session.exec(select(GroupChat).where(GroupChat.id == chat_id)).scalar().owner_id
    )

    return str(owner_id)


@router.get("/create_page")
async def get_create_chat_page(
    request: Request, user_data: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "create_group_chat.html", {"request": request, "user": user_data}
    )


@router.post("/get_username")
def get_username_by_id(
    id: str = Body(..., embed=True), session: Session = Depends(get_session)
):
    user = get_user_by_id(userid=id, session=session)
    return {"username": user.username}
