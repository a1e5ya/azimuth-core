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

# Get the data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/database-stats")
async def get_database_stats(
    current_user: User = Depends(get_current_user)
):
    """Get database statistics"""
    try:
        db_path = DATA_DIR / "finance.db"
        
        # Get file size
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
        return {
            "size": "Unknown",
            "last_backup": "Never"
        }

@router.post("/backup")
async def backup_database(
    current_user: User = Depends(get_current_user)
):
    """Create a backup of the database"""
    try:
        db_path = DATA_DIR / "finance.db"
        
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Database not found")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"finance_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Log the backup
        # Note: We can't use the database here as it's being backed up
        
        return FileResponse(
            path=backup_path,
            filename=backup_filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backup failed: {str(e)}"
        )

@router.post("/restore")
async def restore_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Restore database from backup file"""
    try:
        db_path = DATA_DIR / "finance.db"
        
        # Save uploaded file temporarily
        temp_path = DATA_DIR / f"temp_restore_{datetime.now().timestamp()}.db"
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create a backup of current database before restoring
        if db_path.exists():
            backup_path = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_path)
        
        # Replace current database with uploaded file
        shutil.move(str(temp_path), str(db_path))
        
        return {
            "message": "Database restored successfully"
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Restore failed: {str(e)}"
        )

@router.get("/details")
async def get_system_details(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed system information"""
    try:
        # Get counts
        transaction_count = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
        )
        transactions = transaction_count.scalar_one()
        
        category_count = await db.execute(
            select(func.count(Category.id)).where(Category.user_id == current_user.id)
        )
        categories = category_count.scalar_one()
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system details: {str(e)}"
        )

@router.get("/activity-log/count")
async def get_activity_log_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of activity log entries"""
    try:
        count_query = select(func.count(AuditLog.id)).where(AuditLog.user_id == current_user.id)
        result = await db.execute(count_query)
        count = result.scalar_one()
        
        return {"count": count}
        
    except Exception as e:
        return {"count": 0}

@router.get("/activity-log")
async def get_activity_log(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Get recent activity log entries"""
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get activity log: {str(e)}"
        )

@router.get("/login-history")
async def get_login_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """Get login history"""
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get login history: {str(e)}"
        )