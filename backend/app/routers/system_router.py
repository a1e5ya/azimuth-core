"""
System Router - System Information and Maintenance

Endpoints:
- GET /system/health: Health check endpoint
- GET /system/database-stats: Get database statistics (size, last backup)
- POST /system/backup: Create database backup (download)
- POST /system/restore: Restore database from backup file
- GET /system/details: Get detailed system information
- GET /system/activity-log/count: Get activity log entry count
- GET /system/activity-log: Get recent activity log entries
- GET /system/login-history: Get user login history

Features:
- System health monitoring
- Database statistics
- Backup/restore functionality
- Activity logging
- Login history tracking
- Database size monitoring

Database: SQLite file (data/finance.db)
Backups: Stored in data/backups/
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pathlib import Path
import shutil
from datetime import datetime
from typing import Optional

from ..models.database import get_db, User, Transaction, Category, Account, AuditLog
from ..auth.local_auth import get_current_user

router = APIRouter(prefix="/system", tags=["system"])

# Directory configuration
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns current timestamp and status
    Used by monitoring systems to verify API is responsive
    
    @returns {dict} {status: "ok", timestamp: str}
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ============================================================================
# DATABASE STATISTICS ENDPOINT
# ============================================================================

@router.get("/database-stats")
async def get_database_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get database statistics
    
    Returns:
    - Database file size in MB
    - Last backup timestamp
    
    @param current_user: Injected from JWT token
    @returns {dict} {size: str, last_backup: str}
    """
    try:
        db_path = DATA_DIR / "finance.db"
        
        # Get database file size
        size_bytes = db_path.stat().st_size if db_path.exists() else 0
        size_mb = round(size_bytes / (1024 * 1024), 2)
        
        # Get last backup time
        backup_files = list(BACKUP_DIR.glob("*.db"))
        last_backup = "Never"
        if backup_files:
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            last_backup = backup_time.strftime("%Y-%m-%d %H:%M")
        
        return {
            "size": f"{size_mb} MB",
            "last_backup": last_backup
        }
    except Exception as e:
        print(f"❌ Failed to get database stats: {e}")
        return {
            "size": "Unknown",
            "last_backup": "Never"
        }


# ============================================================================
# DATABASE BACKUP ENDPOINT
# ============================================================================

@router.post("/backup")
async def backup_database(
    current_user: User = Depends(get_current_user)
):
    """
    Create database backup and download
    
    Process:
    1. Copy database file to backup directory
    2. Create timestamped filename
    3. Return as file download
    
    Backup filename: finance_backup_YYYYMMDD_HHMMSS.db
    Backups are stored in data/backups/
    
    @param current_user: Injected from JWT token (auth required)
    @returns {FileResponse} Database backup file
    @raises HTTPException: 404 if database not found, 500 on backup failure
    """
    try:
        db_path = DATA_DIR / "finance.db"
        
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Database not found")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"finance_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename
        
        # Copy database file to backup directory
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Database backup created: {backup_filename}")
        
        # Return file as download
        return FileResponse(
            path=backup_path,
            filename=backup_filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup failed: {str(e)}"
        )


# ============================================================================
# DATABASE RESTORE ENDPOINT
# ============================================================================

@router.post("/restore")
async def restore_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Restore database from backup file
    
    WARNING: This replaces the entire database!
    A safety backup is created before restore
    
    Process:
    1. Save uploaded file to temp location
    2. Create pre-restore backup of current database
    3. Replace current database with uploaded file
    4. Cleanup temp file
    
    Safety backup: pre_restore_YYYYMMDD_HHMMSS.db
    
    @param file: Uploaded backup file (.db)
    @param current_user: Injected from JWT token (auth required)
    @returns {dict} {message}
    @raises HTTPException: 500 on restore failure
    """
    temp_path = None
    try:
        db_path = DATA_DIR / "finance.db"
        
        # Save uploaded file temporarily
        timestamp = datetime.now().timestamp()
        temp_path = DATA_DIR / f"temp_restore_{timestamp}.db"
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create safety backup of current database before restoring
        if db_path.exists():
            backup_path = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_path)
            print(f"✅ Safety backup created: {backup_path.name}")
        
        # Replace current database with uploaded file
        shutil.move(str(temp_path), str(db_path))
        
        print(f"✅ Database restored from: {file.filename}")
        
        return {
            "message": "Database restored successfully"
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path and temp_path.exists():
            temp_path.unlink()
        
        print(f"❌ Restore failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Restore failed: {str(e)}"
        )


# ============================================================================
# DETAILED SYSTEM INFORMATION ENDPOINT
# ============================================================================

@router.get("/details")
async def get_system_details(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed system information
    
    Returns:
    - Database size
    - Uptime (N/A - not tracked)
    - AI model name
    - Category count
    - Account count
    - Transaction count
    
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} System details
    @raises HTTPException: 500 on query failure
    """
    try:
        # Get transaction count
        transaction_count = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
        )
        transactions = transaction_count.scalar_one()
        
        # Get category count
        category_count = await db.execute(
            select(func.count(Category.id)).where(Category.user_id == current_user.id)
        )
        categories = category_count.scalar_one()
        
        # Get account count
        account_count = await db.execute(
            select(func.count(Account.id)).where(Account.user_id == current_user.id)
        )
        accounts = account_count.scalar_one()
        
        # Get database size
        db_path = DATA_DIR / "finance.db"
        size_bytes = db_path.stat().st_size if db_path.exists() else 0
        size_mb = round(size_bytes / (1024 * 1024), 2)
        
        return {
            "databaseSize": f"{size_mb} MB",
            "uptime": "N/A",  # Would need to track server start time
            "aiModel": "llama3.2:3b",  # Could load from settings
            "categories": categories,
            "accounts": accounts,
            "transactions": transactions
        }
        
    except Exception as e:
        print(f"❌ Failed to get system details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system details: {str(e)}"
        )


# ============================================================================
# ACTIVITY LOG ENDPOINTS
# ============================================================================

@router.get("/activity-log/count")
async def get_activity_log_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of activity log entries
    
    Returns total number of audit log entries for current user
    
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {count: int}
    """
    try:
        count_query = select(func.count(AuditLog.id)).where(AuditLog.user_id == current_user.id)
        result = await db.execute(count_query)
        count = result.scalar_one()
        
        return {"count": count}
        
    except Exception as e:
        print(f"❌ Failed to get activity log count: {e}")
        return {"count": 0}


@router.get("/activity-log")
async def get_activity_log(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    Get recent activity log entries
    
    Returns recent audit log entries for current user
    Sorted by created_at descending (newest first)
    
    @param db: Database session
    @param current_user: Injected from JWT token
    @param limit: Number of entries to return (default: 50)
    @returns {list} List of activity log entries
    @raises HTTPException: 500 on query failure
    """
    try:
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == current_user.id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "entity": log.entity,
                "action": log.action,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "Unknown"
            }
            for log in logs
        ]
        
    except Exception as e:
        print(f"❌ Failed to get activity log: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get activity log: {str(e)}"
        )


# ============================================================================
# LOGIN HISTORY ENDPOINT
# ============================================================================

@router.get("/login-history")
async def get_login_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """
    Get user login history
    
    Returns recent login and signup events from audit log
    Sorted by created_at descending (newest first)
    
    @param db: Database session
    @param current_user: Injected from JWT token
    @param limit: Number of entries to return (default: 20)
    @returns {list} List of login history entries
    @raises HTTPException: 500 on query failure
    """
    try:
        query = (
            select(AuditLog)
            .where(
                AuditLog.user_id == current_user.id,
                AuditLog.entity == "auth",
                AuditLog.action.in_(["login", "signup"])
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "action": log.action.capitalize(),
                "ip_address": log.ip_address or "Unknown",
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "Unknown"
            }
            for log in logs
        ]
        
    except Exception as e:
        print(f"❌ Failed to get login history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get login history: {str(e)}"
        )