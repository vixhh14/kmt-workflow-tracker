from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.database import get_db
from app.models.models_db import User, Machine

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/sheets")
async def health_check_sheets(db: Any = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check to verify Google Sheets connection and data integrity.
    Reads users and machines sheets and returns counts.
    """
    try:
        # Read users
        users = db.query(User).all()
        user_count = len(users)
        active_users = len([u for u in users if getattr(u, 'is_active', False)])
        
        # Read machines
        machines = db.query(Machine).all()
        machine_count = len(machines)
        active_machines = len([m for m in machines if getattr(m, 'is_active', False)])
        
        # Check connection implicitly by performing these reads
        return {
            "status": "healthy",
            "database": "Google Sheets",
            "counts": {
                "users": {
                    "total": user_count,
                    "active": active_users
                },
                "machines": {
                    "total": machine_count,
                    "active": active_machines
                }
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "Google Sheets",
            "error": str(e)
        }
