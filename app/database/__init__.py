from app.database.base import Base
from app.database.connection import SessionLocal, engine


def create_tables() -> None:
    # Import all models so SQLAlchemy registers their tables.
    Base.metadata.create_all(bind=engine)


__all__ = ["Base", "SessionLocal", "engine", "create_tables"]
