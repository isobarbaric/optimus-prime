"""Database session management using SQLModel."""
import os
from sqlmodel import Session, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./todos.db")

_engine = create_engine(DATABASE_URL, echo=False)


class DatabaseSession:
    """Manages SQLModel database sessions with automatic rollback on error."""

    def __init__(self, engine=None) -> None:
        """Initialize with an optional custom engine; defaults to the module-level engine."""
        self._engine = engine or _engine

    def get_session(self):
        """Yield a SQLModel session, rolling back on any unhandled exception.

        Designed to be used as a FastAPI dependency via get_db_session().
        """
        with Session(self._engine) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise


_db_session = DatabaseSession()


def get_db_session():
    """FastAPI dependency that yields a managed SQLModel database session.

    Rolls back the session automatically if an exception occurs during
    the request lifecycle, then re-raises the exception.
    """
    yield from _db_session.get_session()
