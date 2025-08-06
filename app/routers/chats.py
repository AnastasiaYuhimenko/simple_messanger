from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from sqlmodel import Session, select
from db import get_session
from models.allmodels import User, Chat
from schemas.users import UserOut
from services.users import get_current_user, get_user_by_name

router = APIRouter()


@router.post("/create_chat")
async def create_chat(
    current_user: Annotated[UserOut, Depends(get_current_user)],
    user2_username: str,
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
