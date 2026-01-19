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
@router.get("/schema")
async def health_check_schema() -> Dict[str, Any]:
    """
    Returns schema health status for critical sheets.
    If mismatch detected, frontend should refuse to operate.
    """
    from app.core.sheets_config import SHEETS_SCHEMA
    from app.services.google_sheets import google_sheets
    
    results = {}
    try:
        for sheet_name, expected_headers in SHEETS_SCHEMA.items():
            try:
                worksheet = google_sheets.get_worksheet(sheet_name)
                all_vals = worksheet.get_all_values()
                actual_headers = all_vals[0] if all_vals else []
                
                match = True
                if len(actual_headers) < len(expected_headers):
                    match = False
                else:
                    for i, h in enumerate(expected_headers):
                        if actual_headers[i].strip().lower() != h.strip().lower():
                            match = False
                            break
                
                results[sheet_name] = "OK" if match else "ERROR: Header Mismatch"
            except:
                results[sheet_name] = "ERROR: Missing Worksheet"
        
        return results
    except Exception as e:
        return {"error": str(e)}
