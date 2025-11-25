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

@router.get("/export")
async def export_database(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export entire database as a downloadable file"""
    try:
        db_path = DATA_DIR / "finance.db"
        
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Database file not found")
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"azimuth_backup_{timestamp}.db"
        backup_path = DATA_DIR / backup_filename
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        return FileResponse(
            path=backup_path,
            filename=backup_filename,
            media_type="application/octet-stream",
            background=lambda: os.remove(backup_path)  # Cleanup after download
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.post("/import")
async def import_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Restore database from uploaded backup file"""
    try:
        # Validate file extension
        if not file.filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Invalid file type. Must be .db file")
        
        db_path = DATA_DIR / "finance.db"
        
        # Create backup of current database before restore
        if db_path.exists():
            backup_current = DATA_DIR / f"finance_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_current)
        
        # Save uploaded file as new database
        temp_path = DATA_DIR / "temp_restore.db"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Close all database connections
        await db.close()
        
        # Replace current database
        shutil.move(str(temp_path), str(db_path))
        
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
        
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")