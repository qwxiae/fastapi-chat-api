from sqlalchemy import create_engine 
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings
from typing import Generator, Any

class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    echo=True,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    
)

def get_db() -> Generator[Session, Any, Any]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        