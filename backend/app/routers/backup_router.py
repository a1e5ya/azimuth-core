"""
Backup Router - Database Export and Restore

Endpoints:
- GET /backup/export: Download database backup file
- POST /backup/import: Restore database from uploaded backup

Features:
- Full database export as .db file
- Timestamped backup filenames
- Automatic cleanup after download
- Safe restore with pre-restore backup
- Database connection handling during restore

Security:
- Requires authentication
- Creates safety backup before restore
- Validates file extension (.db only)

Database: SQLite file (data/finance.db)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, User, DATA_DIR
from app.routers.auth import get_current_user
import shutil
from pathlib import Path
from datetime import datetime
import os

router = APIRouter(prefix="/backup", tags=["backup"])


# ============================================================================
# DATABASE EXPORT ENDPOINT
# ============================================================================

@router.get("/export")
async def export_database(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export entire database as downloadable file
    
    Process:
    1. Locate database file (data/finance.db)
    2. Create timestamped copy
    3. Return as download (FileResponse)
    4. Cleanup temp file after download
    
    Filename format: azimuth_backup_YYYYMMDD_HHMMSS.db
    
    @param current_user: Injected from JWT token (auth required)
    @param db: Database session
    @returns {FileResponse} Database file download
    @raises HTTPException: 404 if database file not found, 500 on backup failure
    """
    try:
        db_path = DATA_DIR / "finance.db"
        
        # Check if database file exists
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Database file not found")
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"azimuth_backup_{timestamp}.db"
        backup_path = DATA_DIR / backup_filename
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Database exported: {backup_filename}")
        
        # Return file with automatic cleanup after download
        return FileResponse(
            path=backup_path,
            filename=backup_filename,
            media_type="application/octet-stream",
            background=lambda: os.remove(backup_path)  # Cleanup temp file
        )
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


# ============================================================================
# DATABASE IMPORT ENDPOINT
# ============================================================================

@router.post("/import")
async def import_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Restore database from uploaded backup file
    
    Process:
    1. Validate file extension (.db only)
    2. Create safety backup of current database
    3. Close all database connections
    4. Replace current database with uploaded file
    5. Cleanup temp files
    
    WARNING: This replaces the entire database!
    A safety backup is created before restore
    
    Safety backup format: finance_before_restore_YYYYMMDD_HHMMSS.db
    
    @param file: Uploaded .db file
    @param current_user: Injected from JWT token (auth required)
    @param db: Database session
    @returns {dict} Success message with filename
    @raises HTTPException: 400 if invalid file type, 500 on restore failure
    """
    try:
        # Validate file extension
        if not file.filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Invalid file type. Must be .db file")
        
        db_path = DATA_DIR / "finance.db"
        
        # Create safety backup of current database before restore
        if db_path.exists():
            backup_current = DATA_DIR / f"finance_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_current)
            print(f"✅ Safety backup created: {backup_current.name}")
        
        # Save uploaded file to temp location
        temp_path = DATA_DIR / "temp_restore.db"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Close all database connections
        await db.close()
        
        # Replace current database with uploaded file
        shutil.move(str(temp_path), str(db_path))
        
        print(f"✅ Database restored from: {file.filename}")
        
        return {
            "success": True,
            "message": "Database restored successfully. Please refresh the page.",
            "filename": file.filename
        }
        
    except Exception as e:
        # Cleanup temp file if exists
        temp_path = DATA_DIR / "temp_restore.db"
        if temp_path.exists():
            os.remove(temp_path)
        
        print(f"❌ Restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")