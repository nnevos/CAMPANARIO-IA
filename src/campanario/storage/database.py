from collections.abc import Callable

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from campanario.config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    if database_url is None:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    url = database_url or f"sqlite:///{settings.database_path.as_posix()}"
    engine = create_engine(url, future=True)

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_session_factory(engine: Engine) -> Callable[[], Session]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return factory
