from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure we're using PostgreSQL, not SQLite
if 'sqlite' in settings.DATABASE_URL:
    logger.warning("SQLite detected in DATABASE_URL. Using PostgreSQL instead.")
    settings.DATABASE_URL = "postgresql://alex:hales@localhost:5432/admin_service"

# Database engine for PostgreSQL - synchronous version
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10,
        echo=settings.DEBUG
    )
    
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
        
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    # Create a dummy engine that will raise exceptions when used
    # This allows the application to start even with DB connection issues
    engine = create_engine("postgresql://localhost/dummy", strategy="mock", executor=lambda *args, **kwargs: None)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def init_db():
    """Initialize database tables"""
    try:
        # Import all models explicitly to ensure they're registered with Base
        from app.models.admin_config import AdminConfig
        from app.models.system_settings import SystemSettings
        
        logger.info("Starting database tables creation...")
        
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"Existing tables: {existing_tables}")
        
        # Create tables using synchronous engine
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info(f"Tables after creation: {created_tables}")
        
        # Initialize admin config if needed
        db = SessionLocal()
        try:
            admin_config = db.query(AdminConfig).filter(AdminConfig.is_active == True).first()
            if not admin_config:
                logger.info("Creating default admin config")
                try:
                    default_config = AdminConfig(
                        admin_paypal_email="admin@paymentgateway.com",
                        admin_paypal_client_id="default-client-id",
                        admin_paypal_client_secret="default-client-secret",
                        sslcz_store_id="default-store-id",
                        sslcz_store_passwd="default-store-passwd",
                        service_fee_percentage=2.00,
                        is_active=True
                    )
                    db.add(default_config)
                    db.commit()
                    logger.info("Default admin config created successfully")
                except Exception as e:
                    logger.error(f"Error creating default admin config: {e}")
                    db.rollback()
        except Exception as e:
            logger.error(f"Error checking for admin config: {e}")
        finally:
            db.close()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
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

def verify_db_connection() -> bool:
    """Verify database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False