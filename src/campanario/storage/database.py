from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from campanario.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine():
    settings = get_settings()
    url = f"sqlite:///{settings.database_path.as_posix()}"
    return create_engine(url, future=True)


def build_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
