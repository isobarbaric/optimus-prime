"""Database session management for SQLModel ORM."""
import os
from collections.abc import Generator

from sqlmodel import Session, create_engine


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./todos.db")

_engine = create_engine(DATABASE_URL, echo=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a SQLModel database session for injection via FastAPI Depends().

    Rolls back the active transaction on exception before closing the session,
    ensuring the database is never left in a partially-committed state.
    """
    with Session(_engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
