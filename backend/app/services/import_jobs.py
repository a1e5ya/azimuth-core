"""
Import Job Storage - In-Memory Job Status Tracking

Tracks long-running CSV/XLSX import jobs with progress updates.

Features:
- Create import job with unique job_id
- Update job progress (step, percentage)
- Get job status for polling
- Mark job complete/failed
- Store results

Storage: In-memory dictionary (use Redis in production)

Job lifecycle:
1. create_job() → returns job_id
2. update_job() → update progress during import
3. complete_job() or fail_job() → finalize status
4. get_job() → frontend polls for status

Used by: TransactionImportService for async imports
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# ============================================================================
# IN-MEMORY JOB STORAGE
# ============================================================================
# NOTE: In production, replace with Redis for:
# - Persistence across server restarts
# - Multi-instance support
# - Automatic expiration

import_jobs: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# JOB MANAGEMENT FUNCTIONS
# ============================================================================

def create_job(user_id: str) -> str:
    """
    Create new import job and return job_id
    
    Initializes job with default status:
    - status: "processing"
    - progress: 0
    - current_step: "uploading"
    
    @param user_id: User UUID (for filtering jobs)
    @returns {str} Unique job_id (UUID)
    """
    job_id = str(uuid.uuid4())
    
    import_jobs[job_id] = {
        "user_id": user_id,
        "status": "processing",  # processing|complete|failed
        "progress": 0,  # 0-100 percentage
        "total": 0,  # Total rows to process
        "current_step": "uploading",  # uploading|parsing|processing|categorizing|saving
        "message": "Starting import...",
        "result": None,  # Final result dict
        "error": None,  # Error message if failed
        "created_at": datetime.utcnow().isoformat()
    }
    
    return job_id


def update_job(job_id: str, updates: Dict[str, Any]):
    """
    Update job status with partial updates
    
    Common updates:
    - {"progress": 50, "message": "Processing row 500/1000"}
    - {"current_step": "categorizing", "message": "Auto-categorizing..."}
    - {"progress": 75, "message": "Saving to database..."}
    
    @param job_id: Job UUID
    @param updates: Dict of fields to update
    """
    if job_id in import_jobs:
        import_jobs[job_id].update(updates)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current job status
    
    Used by frontend to poll for progress updates
    Returns None if job not found (expired or invalid)
    
    @param job_id: Job UUID
    @returns {dict|None} Job status dict or None
    """
    return import_jobs.get(job_id)


def complete_job(job_id: str, result: Dict[str, Any]):
    """
    Mark job as complete with final results
    
    Updates:
    - status: "complete"
    - message: "Import complete!"
    - result: Import summary (rows imported, duplicates, errors)
    - completed_at: Timestamp
    
    @param job_id: Job UUID
    @param result: Final import result dict
    """
    if job_id in import_jobs:
        import_jobs[job_id].update({
            "status": "complete",
            "message": "Import complete!",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        })


def fail_job(job_id: str, error: str):
    """
    Mark job as failed with error message
    
    Updates:
    - status: "failed"
    - message: Error message
    - error: Error details
    - failed_at: Timestamp
    
    @param job_id: Job UUID
    @param error: Error message
    """
    if job_id in import_jobs:
        import_jobs[job_id].update({
            "status": "failed",
            "message": error,
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        })


# ============================================================================
# CLEANUP UTILITIES (Optional)
# ============================================================================

def cleanup_old_jobs(hours: int = 24):
    """
    Remove jobs older than specified hours
    
    Prevents memory leak from accumulating completed jobs
    Should be called periodically (e.g., daily cron job)
    
    @param hours: Age threshold in hours (default: 24)
    @returns {int} Number of jobs cleaned up
    """
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    cleaned = 0
    
    for job_id, job in list(import_jobs.items()):
        created_at = datetime.fromisoformat(job["created_at"])
        if created_at < cutoff:
            del import_jobs[job_id]
            cleaned += 1
    
    return cleaned


def get_user_jobs(user_id: str) -> list:
    """
    Get all jobs for a specific user
    
    Useful for showing user's import history
    
    @param user_id: User UUID
    @returns {list} List of job dicts
    """
    return [
        {"job_id": job_id, **job}
        for job_id, job in import_jobs.items()
        if job.get("user_id") == user_id
    ]