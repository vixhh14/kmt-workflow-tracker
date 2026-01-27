
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.models_db import Attendance, User
from app.core.time_utils import get_current_time_ist, get_today_date_ist
from app.core.sheets_db import SheetsDB

def mark_present(db: SheetsDB, user_id: str, ip_address: Optional[str] = None) -> dict:
    """
    Mark user as present for today (IST). Idempotent.
    Canonical columns: [attendance_id, user_id, date, login_time, logout_time, status]
    """
    try:
        from app.repositories.sheets_repository import sheets_repo
        today_str = get_today_date_ist().isoformat()
        now_ist = get_current_time_ist().isoformat()
        
        def normalize_date_str(d_str):
            if not d_str: return ""
            s = str(d_str).strip().split('T')[0]
            if '/' in s:
                p = s.split('/')
                if len(p) == 3:
                     try: return f"{p[2]}-{int(p[1]):02d}-{int(p[0]):02d}"
                     except: pass
            return s

        # 1. Fetch all attendance for today (cached)
        all_att = sheets_repo.get_all("attendance")
        
        existing = next((a for a in all_att if str(a.get("user_id")) == str(user_id) and normalize_date_str(a.get("date")) == today_str), None)
        
        if existing:
            # Update missing login_time or status
            updates = {}
            if not existing.get("login_time"):
                updates["login_time"] = now_ist
            if str(existing.get("status", "")).lower() != "present":
                updates["status"] = "Present"
            
            if updates:
                sheets_repo.update("attendance", existing["attendance_id"], updates)
            return {"status": "success", "message": "Attendance marked", "data": existing}
        
        # 2. Create new record
        att_id = f"att_{user_id}_{today_str.replace('-', '')}"
        record = {
            "attendance_id": att_id,
            "user_id": str(user_id),
            "date": today_str,
            "login_time": now_ist,
            "logout_time": "",
            "status": "Present"
        }
        
        inserted = sheets_repo.insert("attendance", record)
        return {"status": "success", "message": "Checked in successfully", "data": inserted}
    
    except Exception as e:
        print(f"❌ Error in mark_present: {e}")
        return {"success": False, "message": str(e)}


def mark_checkout(db: SheetsDB, user_id: str) -> dict:
    """
    Mark user as checked out for today (IST).
    """
    try:
        from app.repositories.sheets_repository import sheets_repo
        today_str = get_today_date_ist().isoformat()
        now_ist = get_current_time_ist().isoformat()
        
        all_att = sheets_repo.get_all("attendance")
        existing = next((a for a in all_att if str(a.get("user_id")) == str(user_id) and str(a.get("date")) == today_str), None)

        if not existing:
            return {"status": "error", "message": "No check-in record found for today"}

        if existing.get("logout_time"):
            return {"status": "success", "message": "Already checked out", "data": existing}

        sheets_repo.update("attendance", existing["attendance_id"], {
            "logout_time": now_ist
        })
        
        return {"status": "success", "message": "Checked out successfully"}
    
    except Exception as e:
        print(f"❌ Error in mark_checkout: {e}")
        return {"success": False, "message": str(e)}


def get_attendance_summary(db: SheetsDB, target_date_str: Optional[str] = None):
    """
    Get attendance summary for a specific date (YYYY-MM-DD). Defaults to today.
    CRITICAL FIX: Extremely lenient filtering to ensure users are shown
    """
    try:
        if not target_date_str:
            target_date_str = get_today_date_ist().isoformat()
            
        target_date_compare = str(target_date_str).split('T')[0]
        
        # 1. Fetch all users and attendance
        from app.repositories.sheets_repository import sheets_repo
        all_users = sheets_repo.get_all("users")
        all_att = sheets_repo.get_all("attendance")
        
        print(f"\n{'='*60}")
        print(f"🔍 ATTENDANCE DEBUG - Date: {target_date_compare}")
        print(f"{'='*60}")
        print(f"📊 Total users in system: {len(all_users)}")
        print(f"📊 Total attendance records: {len(all_att)}")
        
        def normalize_date_str(d_str):
            if not d_str: return ""
            s = str(d_str).strip().split('T')[0]
            if '/' in s:
                p = s.split('/')
                if len(p) == 3:
                     try:
                         # Handle D/M/YYYY or DD/MM/YYYY
                         return f"{p[2]}-{int(p[1]):02d}-{int(p[0]):02d}"
                     except: pass
            return s

        attendance_map = {}
        for a in all_att:
            # 1. Date normalization (ensure match even with time or different formats)
            raw_date = normalize_date_str(a.get("date", ""))
            if raw_date == target_date_compare:
                # 2. Map by user_id primarily, fallback to username
                uid = str(a.get("user_id", "")).strip().lower()
                if uid:
                    attendance_map[uid] = a
                
                uname = str(a.get("username", "")).strip().lower()
                if uname and uname not in attendance_map:
                    attendance_map[uname] = a
        
        print(f"📊 Attendance records for {target_date_compare}: {len(attendance_map)}")
        
        present_records = []
        absent_users = []
        
        filtered_count = 0
        for user in all_users:
            # Try multiple ID aliases
            user_id = str(user.get("user_id") or user.get("id") or "").strip().lower()
            username = str(user.get("username", "Unknown")).strip().lower()
            
            if not user_id and not username:
                continue

            # 1. Soft Delete Check
            is_deleted = str(user.get("is_deleted", "false")).lower().strip()
            if is_deleted in ["true", "1", "yes"]:
                filtered_count += 1
                continue
            
            # 2. Active Check
            is_active = str(user.get("active", "true")).lower().strip()
            if is_active in ["false", "0", "no", "inactive"]:
                filtered_count += 1
                continue
            
            # 3. Role check (Removed filtering, but keep role for display)
            role = str(user.get("role", "user")).lower().strip()
                
            # Check attendance map by ID or Username
            att = attendance_map.get(user_id)
            if not att and username:
                att = attendance_map.get(username)
            
            if att and str(att.get("status", "")).lower() == "present":
                present_records.append({
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "login_time": str(att.get("login_time", "")),
                    "logout_time": str(att.get("logout_time", "")),
                    "status": "Present",
                    "date": target_date_compare
                })
                print(f"  ✅ PRESENT: {username} ({role})")
            else:
                absent_users.append({
                    "user_id": user_id,
                    "username": username,
                    "role": role
                })
                print(f"  ⚪ ABSENT: {username} ({role})")

        print(f"\n{'='*60}")
        print(f"📊 FINAL COUNTS:")
        print(f"  Total users checked: {len(all_users)}")
        print(f"  Filtered out: {filtered_count}")
        print(f"  Present: {len(present_records)}")
        print(f"  Absent: {len(absent_users)}")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "date": target_date_compare,
            "present_count": len(present_records),
            "absent_count": len(absent_users),
            "present": len(present_records),
            "absent": len(absent_users),
            "total_tracked": len(present_records) + len(absent_users),
            "records": present_records,
            "all_records": present_records + [{"user_id": u["user_id"], "username": u["username"], "status": "Absent", "role": u["role"]} for u in absent_users],
            "present_users": present_records,
            "absent_users": absent_users
        }
    except Exception as e:
        print(f"❌ Error in get_attendance_summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False, 
            "error": str(e), 
            "present_count": 0, 
            "absent_count": 0, 
            "total_tracked": 0,
            "present_users": [], 
            "absent_users": []
        }

def get_all_attendance(db: SheetsDB, target_date_str: Optional[str] = None):
    """Fetch all attendance records with user info injected."""
    return get_attendance_summary(db, target_date_str).get("records", [])
