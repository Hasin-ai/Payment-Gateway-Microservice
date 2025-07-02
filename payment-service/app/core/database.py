from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import exc
import logging
import asyncio
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def wait_for_db(max_attempts: int = 30, delay: int = 2):
    for attempt in range(max_attempts):
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection successful")
            return True
        except exc.OperationalError as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_attempts} failed: {e}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Failed to connect to database after all attempts")
                raise
    return False

async def init_db():
    try:
        await wait_for_db()
        from app.models import payment
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    try:
        return SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise
