"""
Import Job Storage - In-memory job status tracking
"""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# In-memory job storage (use Redis in production)
import_jobs: Dict[str, Dict[str, Any]] = {}


def create_job(user_id: str) -> str:
    """Create new import job and return job_id"""
    job_id = str(uuid.uuid4())
    
    import_jobs[job_id] = {
        "user_id": user_id,
        "status": "processing",
        "progress": 0,
        "total": 0,
        "current_step": "uploading",
        "message": "Starting import...",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return job_id


def update_job(job_id: str, updates: Dict[str, Any]):
    """Update job status"""
    if job_id in import_jobs:
        import_jobs[job_id].update(updates)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status"""
    return import_jobs.get(job_id)


def complete_job(job_id: str, result: Dict[str, Any]):
    """Mark job as complete"""
    if job_id in import_jobs:
        import_jobs[job_id].update({
            "status": "complete",
            "message": "Import complete!",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        })


def fail_job(job_id: str, error: str):
    """Mark job as failed"""
    if job_id in import_jobs:
        import_jobs[job_id].update({
            "status": "failed",
            "message": error,
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        })