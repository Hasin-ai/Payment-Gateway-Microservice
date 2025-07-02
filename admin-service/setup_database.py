#!/usr/bin/env python

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Parse the database URL
def parse_db_url(url):
    if not url.startswith('postgresql://'):
        raise ValueError("Only PostgreSQL URLs are supported")
    
    url = url[len('postgresql://'):]
    auth, rest = url.split('@', 1) if '@' in url else (None, url)
    
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
    # Get database URL from environment or use default
    db_url = os.environ.get('DATABASE_URL', 'postgresql://alex:hales@localhost:5432/admin_service')
    
    # Parse the database URL
    db_config = parse_db_url(db_url)
    
    dbname = db_config.pop('dbname')
    
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cursor.fetchone():
            print(f"Database '{dbname}' already exists")
        else:
            # Create database
            cursor.execute(f"CREATE DATABASE {dbname}")
            print(f"Database '{dbname}' created successfully")
        
        cursor.close()
        conn.close()
        
        # Connect to the new database
        db_config['dbname'] = dbname
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if tables exist by querying system tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            AND table_type='BASE TABLE'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print("Existing tables:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("No tables found. Run the application to create tables.")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Setting up database for Payment Gateway Admin Service")
    success = create_database()
    sys.exit(0 if success else 1)
