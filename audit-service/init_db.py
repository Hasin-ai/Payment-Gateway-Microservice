#!/usr/bin/env python3
"""
Database initialization script for Audit Service

This script:
1. Creates the database if it doesn't exist
2. Creates all necessary tables using SQLAlchemy models
3. Sets up proper indexes for performance
4. Initializes Alembic migration tracking
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(__file__))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import Base, engine
from app.models.audit_log import AuditLog, AuditQueue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create the audit_service database if it doesn't exist"""
    try:
        # Parse database URL to get connection details
        db_url = settings.DATABASE_URL
        url_parts = db_url.replace('postgresql://', '').split('/')
        host_part = url_parts[0]
        database = url_parts[1] if len(url_parts) > 1 else 'audit_service'
        
        if '@' in host_part:
            auth_part, host_port = host_part.split('@')
            username, password = auth_part.split(':')
        else:
            username, password = 'alex', 'hales'
            host_port = host_part
            
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host, port = host_port, '5432'

        # Connect to PostgreSQL server (to default postgres database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{database}'...")
            cursor.execute(f"CREATE DATABASE {database}")
            logger.info(f"Database '{database}' created successfully!")
        else:
            logger.info(f"Database '{database}' already exists.")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False

def create_tables():
    """Create all tables using SQLAlchemy models"""
    try:
        logger.info("Creating database tables...")
        
        # This will create all tables defined in the models
        Base.metadata.create_all(bind=engine)
        
        logger.info("Tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {tables}")
            
            # Verify indexes exist
            result = conn.execute(text("""
                SELECT indexname, tablename
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND indexname NOT LIKE '%_pkey'
                ORDER BY tablename, indexname
            """))
            indexes = result.fetchall()
            if indexes:
                logger.info("Created indexes:")
                for index in indexes:
                    logger.info(f"  - {index[0]} on {index[1]}")
            else:
                logger.warning("No custom indexes found!")
        
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        logger.info("Testing database connection...")
        
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"PostgreSQL version: {version}")
            
            # Test table access
            result = conn.execute(text("SELECT COUNT(*) FROM audit_logs"))
            count = result.fetchone()[0]
            logger.info(f"Current audit_logs count: {count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM audit_queue"))
            count = result.fetchone()[0]
            logger.info(f"Current audit_queue count: {count}")
            
        logger.info("Database connection test successful!")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def setup_sample_data():
    """Insert some sample data for testing"""
    try:
        logger.info("Setting up sample audit data...")
        
        with engine.connect() as conn:
            # Insert a sample audit log
            conn.execute(text("""
                INSERT INTO audit_logs (
                    user_id, action, severity, category, 
                    service_name, is_sensitive, is_successful
                ) VALUES (
                    1, 'database_initialization', 'INFO', 'system',
                    'audit-service', false, true
                )
            """))
            conn.commit()
            
        logger.info("Sample data inserted successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert sample data: {e}")
        return False

def main():
    """Main initialization function"""
    logger.info("Starting Audit Service Database Initialization...")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    # Step 1: Create database if needed
    if not create_database_if_not_exists():
        logger.error("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Create tables
    if not create_tables():
        logger.error("Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Step 3: Test connection
    if not test_database_connection():
        logger.error("Database connection test failed. Exiting.")
        sys.exit(1)
    
    # Step 4: Setup sample data (optional)
    setup_sample_data()
    
    logger.info("Database initialization completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Run 'python3 -m alembic stamp head' to mark current state as migrated")
    logger.info("2. Use 'python3 -m alembic revision --autogenerate -m \"description\"' for future schema changes")
    logger.info("3. Use 'python3 -m alembic upgrade head' to apply migrations")

if __name__ == "__main__":
    main()
