#!/usr/bin/env python3
import psycopg2
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db-setup")

# Parse the database URL from environment or use default - PostgreSQL only
db_url = os.environ.get("DATABASE_URL", "postgresql://alex:hales@localhost:5432/admin_service")

# Ensure we're not using SQLite
if 'sqlite' in db_url:
    logger.warning("SQLite detected in DATABASE_URL. Forcing PostgreSQL")
    db_url = "postgresql://alex:hales@localhost:5432/admin_service"

# Parse database connection parameters from the URL
def parse_db_url(url):
    if not url.startswith('postgresql://'):
        raise ValueError("Only PostgreSQL URLs are supported")
    
    url = url.replace('postgresql://', '')
    auth, rest = url.split('@', 1) if '@' in url else ('', url)
    
    if auth:
        user, password = auth.split(':', 1) if ':' in auth else (auth, '')
    else:
        user, password = '', ''
    
    host_port, dbname = rest.split('/', 1) if '/' in rest else (rest, '')
    
    if ':' in host_port:
        host, port = host_port.split(':')
        port = int(port)
    else:
        host = host_port
        port = 5432
    
    return {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'dbname': dbname
    }

def create_database():
    try:
        # Parse the database URL
        db_params = parse_db_url(db_url)
        dbname = db_params.pop('dbname')
        
        logger.info(f"Connecting to PostgreSQL server at {db_params['host']}:{db_params['port']}")
        
        # Connect to PostgreSQL without specifying a database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True  # Need autocommit for creating database
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{dbname}'")
            cursor.execute(f"CREATE DATABASE {dbname}")
            logger.info(f"Database '{dbname}' created successfully")
        else:
            logger.info(f"Database '{dbname}' already exists")
        
        cursor.close()
        conn.close()
        
        # Connect to the database we created/verified
        db_params['dbname'] = dbname
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check for existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        if tables:
            logger.info("Existing tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        else:
            logger.info("No tables found. They will be created when the application starts.")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Setting up database for Payment Gateway Admin Service")
    success = create_database()
    if success:
        logger.info("Database setup completed successfully")
        sys.exit(0)
    else:
        logger.error("Database setup failed")
        sys.exit(1)
