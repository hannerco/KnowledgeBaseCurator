from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings


DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL,
    pool_pre_ping=True,        # verifica la conexión antes de usarla
    pool_recycle=300,          # recicla conexiones cada 5 minutos
    pool_size=5,
    max_overflow=2)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create tables and ensure schema compatibility for existing databases."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS chat_id INTEGER"))
    except SQLAlchemyError:
        pass

    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_type VARCHAR DEFAULT 'user_upload'"))
    except SQLAlchemyError:
        pass

    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE messages ADD CONSTRAINT messages_chat_id_fkey "
                "FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE"
            ))
    except SQLAlchemyError:
        pass


def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()