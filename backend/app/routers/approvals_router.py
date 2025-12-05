"""
User Approvals Router - API endpoints for user approval workflow
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db_connection

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

class UserApproval(BaseModel):
    id: int
    user_id: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class ApprovalAction(BaseModel):
    notes: Optional[str] = None

@router.get("/pending")
async def get_pending_approvals():
    """Get all pending user approvals with user details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            ua.id, ua.user_id, ua.status, ua.approved_by, ua.approved_at, ua.notes, ua.created_at,
            u.username, u.full_name, u.email, u.date_of_birth, u.address, u.contact_number, u.unit_id
        FROM user_approvals ua
        JOIN users u ON ua.user_id = u.user_id
        WHERE ua.status = 'pending'
        ORDER BY ua.created_at DESC
    """)
    
    approvals = []
    for row in cursor.fetchall():
        approvals.append({
            "id": row[0],
            "user_id": row[1],
            "status": row[2],
            "approved_by": row[3],
            "approved_at": row[4],
            "notes": row[5],
            "created_at": row[6],
            "user": {
                "username": row[7],
                "full_name": row[8],
                "email": row[9],
                "date_of_birth": row[10],
                "address": row[11],
                "contact_number": row[12],
                "unit_id": row[13]
            }
        })
    
    conn.close()
    return approvals

@router.post("/{user_id}/approve")
async def approve_user(user_id: str, action: ApprovalAction, approved_by: str = "admin"):
    """Approve a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update approval record
        cursor.execute("""
            UPDATE user_approvals
            SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP, notes = ?
            WHERE user_id = ?
        """, (approved_by, action.notes, user_id))
        
        # Update user status
        cursor.execute("""
            UPDATE users
            SET approval_status = 'approved'
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        return {"message": f"User {user_id} approved successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@router.post("/{user_id}/reject")
async def reject_user(user_id: str, action: ApprovalAction, rejected_by: str = "admin"):
    """Reject a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update approval record
        cursor.execute("""
            UPDATE user_approvals
            SET status = 'rejected', approved_by = ?, approved_at = CURRENT_TIMESTAMP, notes = ?
            WHERE user_id = ?
        """, (rejected_by, action.notes, user_id))
        
        # Update user status
        cursor.execute("""
            UPDATE users
            SET approval_status = 'rejected'
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        return {"message": f"User {user_id} rejected"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
