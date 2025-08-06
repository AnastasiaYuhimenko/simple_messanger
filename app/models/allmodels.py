from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, ForeignKey
from uuid import uuid4, UUID
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID as saUUID
from sqlalchemy.dialects.postgresql import ARRAY


class User(SQLModel, table=True):
    __tablename__ = "Users"

    id: UUID = Field(
        default_factory=uuid4, sa_column=Column(primary_key=True, index=True)
    )
    username: str = Field(sa_column=Column("username", String, unique=True, index=True))
    email: str = Field(sa_column=Column("email", String, unique=True, index=True))
    hashed_password: str
    img: Optional[str] = Field(
        default="https://www.google.com/imgres?q=%D0%B0%D0%B2%D0%B0%D1%82%D0%B0%D1%80%D0%BA%D0%B0%20&imgurl=https%3A%2F%2Fmedia.istockphoto.com%2Fid%2F1495088043%2Fru%2F%25D0%25B2%25D0%25B5%25D0%25BA%25D1%2582%25D0%25BE%25D1%2580%25D0%25BD%25D0%25B0%25D1%258F%2F%25D0%25B7%25D0%25BD%25D0%25B0%25D1%2587%25D0%25BE%25D0%25BA-%25D0%25BF%25D1%2580%25D0%25BE%25D1%2584%25D0%25B8%25D0%25BB%25D1%258F-%25D0%25BF%25D0%25BE%25D0%25BB%25D1%258C%25D0%25B7%25D0%25BE%25D0%25B2%25D0%25B0%25D1%2582%25D0%25B5%25D0%25BB%25D1%258F-%25D0%25B7%25D0%25BD%25D0%25B0%25D1%2587%25D0%25BE%25D0%25BA-%25D0%25B0%25D0%25B2%25D0%25B0%25D1%2582%25D0%25B0%25D1%2580%25D0%25B0-%25D0%25B8%25D0%25BB%25D0%25B8-%25D1%2587%25D0%25B5%25D0%25BB%25D0%25BE%25D0%25B2%25D0%25B5%25D0%25BA%25D0%25B0-%25D0%25B0%25D0%25B2%25D0%25B0%25D1%2582%25D0%25B0%25D1%2580%25D0%25BA%25D0%25B0-%25D0%25BF%25D0%25BE%25D1%2580%25D1%2582%25D1%2580%25D0%25B5%25D1%2582%25D0%25BD%25D1%258B%25D0%25B9-%25D1%2581%25D0%25B8%25D0%25BC%25D0%25B2%25D0%25BE%25D0%25BB.jpg%3Fs%3D612x612%26w%3D0%26k%3D20%26c%3DDS9psRxdq8gUIBtTsGzzy1UYI37nag-gCQ33xqtkpPk%3D&imgrefurl=https%3A%2F%2Fwww.istockphoto.com%2Fru%2F%25D1%2584%25D0%25BE%25D1%2582%25D0%25BE%25D0%25B3%25D1%2580%25D0%25B0%25D1%2584%25D0%25B8%25D0%25B8%2F%25D0%25B0%25D0%25B2%25D0%25B0%25D1%2582%25D0%25B0%25D1%2580%25D0%25BA%25D0%25B0-%25D1%2584%25D0%25BE%25D1%2582%25D0%25BE%25D0%25B3%25D1%2580%25D0%25B0%25D1%2584%25D0%25B8%25D0%25B8&docid=VzyR715DMn6r7M&tbnid=JnYbuAB5ppWaIM&vet=12ahUKEwje47Sb-d2OAxUK9gIHHa4sD0gQM3oECBUQAA..i&w=612&h=612&hcb=2&ved=2ahUKEwje47Sb-d2OAxUK9gIHHa4sD0gQM3oECBUQAA",
        nullable=True,
    )


class Chat(SQLModel, table=True):
    __tablename__ = "Chats"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    users: list[UUID] = Field(sa_column=Column(ARRAY(saUUID(as_uuid=True))))


class Message(SQLModel, table=True):
    __tablename__ = "Messages"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    sender: UUID = Field(sa_column=Column(saUUID(as_uuid=True), ForeignKey("Users.id")))
    send_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    text: str
    user2: UUID
