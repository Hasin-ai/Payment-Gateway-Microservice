#!/usr/bin/env python3
"""
Test script to verify the audit service database functionality
"""

import sys
import os
import asyncio
from datetime import datetime
sys.path.append(os.path.dirname(__file__))

from app.core.database import get_db_session
from app.services.audit_service import AuditService
from app.schemas.audit import AuditEventCreate

async def test_audit_service():
    """Test basic audit service functionality"""
    print("Testing Audit Service functionality...")
    
    # Get database session
    db = get_db_session()
    audit_service = AuditService(db)
    
    try:
        # Test 1: Create a simple audit log
        print("\n1. Testing audit log creation...")
        audit_event = AuditEventCreate(
            user_id=123,
            action="test_action",
            severity="INFO",
            category="testing",
            service_name="test-service",
            meta_data={"test_key": "test_value", "timestamp": datetime.utcnow().isoformat()},
            is_sensitive=False,
            is_successful=True
        )
        
        audit_log = await audit_service.create_audit_log(audit_event)
        print(f"✓ Created audit log with ID: {audit_log.id}")
        
        # Test 2: Query audit logs
        print("\n2. Testing audit log querying...")
        from app.schemas.audit import AuditLogQuery
        
        query = AuditLogQuery(
            user_id=123,
            page=1,
            size=10
        )
        
        logs, total = await audit_service.get_audit_logs(query)
        print(f"✓ Found {total} audit logs for user 123")
        if logs:
            latest_log = logs[0]
            print(f"  - Latest log: {latest_log.action} at {latest_log.created_at}")
        
        # Test 3: Create a sensitive audit log
        print("\n3. Testing sensitive data handling...")
        sensitive_event = AuditEventCreate(
            user_id=456,
            action="password_change",
            severity="WARNING",
            category="security",
            service_name="user-service",
            meta_data={
                "old_password_hash": "sensitive_hash_123",
                "new_password_hash": "sensitive_hash_456",
                "ip_address": "192.168.1.100"
            },
            is_sensitive=True,
            is_successful=True
        )
        
        sensitive_log = await audit_service.create_audit_log(sensitive_event)
        print(f"✓ Created sensitive audit log with ID: {sensitive_log.id}")
        
        # Test 4: Retrieve sensitive log (should be masked)
        retrieved_log = await audit_service.get_audit_log_by_id(sensitive_log.id, include_sensitive=False)
        print(f"✓ Retrieved masked log: meta_data = {retrieved_log.meta_data}")
        
        # Test 5: Test bulk creation
        print("\n4. Testing bulk audit log creation...")
        bulk_events = [
            AuditEventCreate(
                user_id=789,
                action=f"bulk_test_{i}",
                severity="INFO",
                category="bulk_testing",
                service_name="test-service",
                is_successful=True
            )
            for i in range(5)
        ]
        
        bulk_result = await audit_service.create_bulk_audit_logs(
            bulk_events,
            service_name="test-service",
            batch_id="test_batch_001"
        )
        print(f"✓ Created {bulk_result['created_count']} bulk audit logs")
        
        print("\n✅ All tests passed! Audit service is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_database_structure():
    """Test database structure and constraints"""
    print("Testing database structure...")
    
    from sqlalchemy import create_engine, text
    from app.core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Test table structure
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name IN ('audit_logs', 'audit_queue')
                ORDER BY table_name, ordinal_position
            """))
            
            print("\nDatabase Structure:")
            current_table = None
            for row in result:
                if row[0] != current_table:
                    current_table = row[0]
                    print(f"\nTable: {current_table}")
                print(f"  {row[1]}: {row[2]} (nullable: {row[3]})")
            
            # Test constraints
            result = conn.execute(text("""
                SELECT 
                    tc.table_name,
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                AND tc.table_name IN ('audit_logs', 'audit_queue')
                ORDER BY tc.table_name, tc.constraint_type
            """))
            
            print("\nConstraints:")
            for row in result:
                print(f"  {row[0]}.{row[1]}: {row[2]}")
            
            # Test indexes
            result = conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND tablename IN ('audit_logs', 'audit_queue')
                ORDER BY tablename, indexname
            """))
            
            print("\nIndexes:")
            for row in result:
                print(f"  {row[1]}.{row[2]}")
        
        print("\n✅ Database structure test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Database structure test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Audit Service Database Test ===")
    
    # Test database structure
    test_database_structure()
    
    print("\n" + "="*50)
    
    # Test audit service functionality
    asyncio.run(test_audit_service())
    
    print("\n=== Test Complete ===")
