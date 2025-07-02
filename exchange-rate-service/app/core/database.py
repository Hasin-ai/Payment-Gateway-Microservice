from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Database engine
engine = create_engine(
    settings.get_database_url(),
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def init_db():
    """Initialize database tables"""
    try:
        # Test database connection first
        with engine.connect() as conn:
            logger.info(f"Successfully connected to database: {settings.get_database_url()}")
        
        # Import all models to ensure they are registered
        from app.models import exchange_rate
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error(f"Database URL: {settings.get_database_url()}")
        logger.error("Make sure PostgreSQL is running and accessible")
        raise

def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """Get database session for service use"""
    return SessionLocal()
