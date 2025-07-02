#!/usr/bin/env python3
"""
Startup script for Audit Service

This script ensures the database is properly initialized before starting the service.
It can be used in Docker containers or standalone deployments.
"""

import sys
import os
import logging
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.dirname(__file__))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database is accessible"""
    try:
        from app.core.config import settings
        from sqlalchemy import create_engine, text
        
        logger.info("Checking database connection...")
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("Database connection successful")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def check_tables_exist():
    """Check if required tables exist"""
    try:
        from app.core.config import settings
        from sqlalchemy import create_engine, text
        
        logger.info("Checking if tables exist...")
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('audit_logs', 'audit_queue')
            """))
            tables = [row[0] for row in result.fetchall()]
        
        required_tables = {'audit_logs', 'audit_queue'}
        existing_tables = set(tables)
        
        if required_tables.issubset(existing_tables):
            logger.info("All required tables exist")
            return True
        else:
            missing = required_tables - existing_tables
            logger.warning(f"Missing tables: {missing}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to check tables: {e}")
        return False

def initialize_database():
    """Initialize database if needed"""
    try:
        logger.info("Initializing database...")
        
        # Import database initialization
        from app.core.database import Base, engine
        from app.models.audit_log import AuditLog, AuditQueue
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

async def run_migrations():
    """Run any pending database migrations"""
    try:
        import subprocess
        
        logger.info("Checking for pending migrations...")
        
        # Check if alembic is configured
        alembic_ini = Path("alembic.ini")
        if not alembic_ini.exists():
            logger.info("Alembic not configured, skipping migrations")
            return True
        
        # Run migrations
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Migrations completed successfully")
            return True
        else:
            logger.error(f"Migration failed: {result.stderr}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        return False

async def start_service():
    """Start the FastAPI service"""
    try:
        import uvicorn
        from app.main import app
        from app.core.config import settings
        
        logger.info(f"Starting Audit Service on port {settings.SERVICE_PORT}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.SERVICE_PORT,
            log_level="info" if not settings.DEBUG else "debug"
        )
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)

async def main():
    """Main startup function"""
    logger.info("=== Audit Service Startup ===")
    
    # Step 1: Check database connection
    if not check_database_connection():
        logger.error("Cannot connect to database. Please check configuration.")
        sys.exit(1)
    
    # Step 2: Check if tables exist
    if not check_tables_exist():
        logger.info("Tables missing, initializing database...")
        if not initialize_database():
            logger.error("Failed to initialize database")
            sys.exit(1)
    
    # Step 3: Run migrations
    if not await run_migrations():
        logger.warning("Migration check failed, but continuing...")
    
    # Step 4: Start the service
    logger.info("Database ready, starting service...")
    await start_service()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service shutdown requested")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)
