# Audit Service Database Setup

This document provides instructions for setting up and managing the Audit Service database.

## Overview

The Audit Service uses PostgreSQL as its primary database with the following tables:
- `audit_logs`: Main audit logging table with comprehensive audit trail information
- `audit_queue`: Queue table for processing audit events asynchronously

## Database Issues Fixed

### 1. Fixed SQLAlchemy Model Issues
- **Problem**: The `metadata` column name conflicts with SQLAlchemy's reserved `metadata` attribute
- **Solution**: Renamed the column to `meta_data` throughout the codebase
- **Files Updated**: 
  - `app/models/audit_log.py`
  - `app/schemas/audit.py`
  - `app/services/audit_service.py`
  - `app/tasks/audit_processor.py`

### 2. Fixed Boolean Column Types
- **Problem**: Boolean fields were defined as `String(20)` instead of proper `Boolean` type
- **Solution**: Updated `is_sensitive` and `is_successful` columns to use `Boolean` type
- **Files Updated**: `app/models/audit_log.py`

### 3. Added Database Initialization Scripts
- **Problem**: No proper database setup and migration management
- **Solution**: Created comprehensive initialization and migration setup
- **Files Added**:
  - `init_db.py`: Database initialization script
  - `test_audit_service.py`: Comprehensive functionality tests
  - Alembic configuration for migrations

## Quick Setup

### 1. Install Dependencies
```bash
cd /path/to/audit-service
pip install -r requirements.txt
```

### 2. Configure Database
Update the `.env` file or environment variables:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/audit_service
```

### 3. Initialize Database
```bash
# Using the initialization script
python init_db.py

# Or manually with Python virtual environment
/path/to/.venv/bin/python init_db.py
```

### 4. Setup Migrations (Already Done)
```bash
# Mark current state as migrated
python -m alembic stamp head
```

## Database Schema

### audit_logs Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    session_id VARCHAR(100),
    service_name VARCHAR(50),
    endpoint VARCHAR(200),
    method VARCHAR(10),
    meta_data JSONB,
    severity VARCHAR(20) DEFAULT 'INFO',
    category VARCHAR(50),
    compliance_tags JSONB,
    is_sensitive BOOLEAN DEFAULT FALSE,
    is_successful BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### audit_queue Table
```sql
CREATE TABLE audit_queue (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    payload JSONB NOT NULL,
    source_service VARCHAR(50),
    status VARCHAR(20) DEFAULT 'PENDING',
    processing_attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);
```

### Indexes Created
- `ix_audit_logs_user_id`: Index on user_id for user activity queries
- `ix_audit_logs_action`: Index on action for action-based queries
- `ix_audit_logs_created_at`: Index on created_at for time-based queries
- `idx_audit_logs_user_action`: Composite index on (user_id, action)
- `idx_audit_logs_table_record`: Composite index on (table_name, record_id)
- `idx_audit_logs_created_severity`: Composite index on (created_at, severity)
- `idx_audit_logs_category_created`: Composite index on (category, created_at)
- `idx_audit_queue_status_priority`: Composite index on (status, priority)

## Testing the Database

Run the comprehensive test suite:
```bash
python test_audit_service.py
```

This test covers:
- Database structure validation
- Audit log creation and querying
- Sensitive data masking
- Bulk operations
- Security features

## Migration Management

### Creating New Migrations
When you modify the database models:
```bash
# Auto-generate migration
python -m alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/

# Apply the migration
python -m alembic upgrade head
```

### Migration Commands
```bash
# Show current migration status
python -m alembic current

# Show migration history
python -m alembic history

# Upgrade to latest
python -m alembic upgrade head

# Downgrade one revision
python -m alembic downgrade -1

# Upgrade to specific revision
python -m alembic upgrade <revision_id>
```

## Performance Considerations

### Indexes
The database includes optimized indexes for common query patterns:
- User activity queries (user_id + action)
- Time-based queries (created_at)
- Severity filtering (created_at + severity)
- Table/record tracking (table_name + record_id)
- Queue processing (status + priority)

### Data Retention
- Configure `AUDIT_RETENTION_DAYS` in settings (default: 365 days)
- Use the cleanup endpoint: `DELETE /api/v1/audit/cleanup?days=365&dry_run=false`
- Consider archiving old data instead of deletion for compliance

### Partitioning (Recommended for High Volume)
For high-volume environments, consider partitioning the audit_logs table by date:
```sql
-- Example monthly partitioning (implement as needed)
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Backup and Recovery

### Daily Backup
```bash
pg_dump -h localhost -U username audit_service > audit_service_backup_$(date +%Y%m%d).sql
```

### Restore
```bash
psql -h localhost -U username -d audit_service < audit_service_backup_YYYYMMDD.sql
```

## Monitoring

### Key Metrics to Monitor
- Table sizes: `SELECT pg_size_pretty(pg_total_relation_size('audit_logs'));`
- Query performance: Monitor slow queries with `pg_stat_statements`
- Index usage: Monitor with `pg_stat_user_indexes`
- Connection count: Monitor active connections

### Health Check Queries
```sql
-- Check recent activity
SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour';

-- Check queue status
SELECT status, COUNT(*) FROM audit_queue GROUP BY status;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';
```

## Security Considerations

### Data Masking
- Sensitive data is automatically masked when `MASK_SENSITIVE_DATA=true`
- Configure sensitive fields in `SENSITIVE_FIELDS` setting
- Use `include_sensitive=false` (default) for API queries

### Access Control
- Use database-level permissions to restrict access
- Implement application-level role-based access control
- Audit administrative actions

### Compliance
- Enable compliance tags: PCI, GDPR, etc.
- Configure retention policies according to compliance requirements
- Implement data export capabilities for compliance audits

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify connection parameters in `.env`
   - Check firewall and network connectivity

2. **Permission Denied**
   - Verify database user has necessary permissions
   - Check if database exists: `psql -l | grep audit_service`

3. **Migration Conflicts**
   - Check current migration status: `python -m alembic current`
   - Resolve conflicts manually if needed
   - Use `alembic stamp head` to mark current state

4. **Performance Issues**
   - Check query execution plans: `EXPLAIN ANALYZE SELECT ...`
   - Monitor index usage: `SELECT * FROM pg_stat_user_indexes;`
   - Consider adding specific indexes for custom queries

### Logs and Debugging
- Enable SQL logging: Set `DEBUG=true` in configuration
- Check PostgreSQL logs: Usually in `/var/log/postgresql/`
- Use application logs for audit service specific issues

## Development

### Local Development Setup
1. Install PostgreSQL locally
2. Create development database
3. Run initialization script
4. Use test data for development

### Testing
- Run `test_audit_service.py` for functionality tests
- Use `init_db.py` to reset development database
- Consider using Docker for consistent environments

---

## Summary

The Audit Service database has been successfully set up with:
- ✅ Fixed SQLAlchemy model issues (metadata → meta_data)
- ✅ Corrected column types (Boolean fields)
- ✅ Created comprehensive database schema
- ✅ Set up proper indexes for performance
- ✅ Implemented Alembic migrations
- ✅ Added initialization and testing scripts
- ✅ Comprehensive documentation

The database is now ready for production use with proper audit logging, security features, and compliance capabilities.
