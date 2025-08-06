from sqlmodel import Session, create_engine
from config import settings
from typing import Annotated
from fastapi import Depends

engine = create_engine(settings.POSTGRES_URL)
DBSession = Session


async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
