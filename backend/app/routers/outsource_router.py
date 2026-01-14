from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any
from datetime import datetime
import uuid
from app.models.outsource_model import OutsourceCreate, OutsourceUpdate
from app.models.models_db import OutsourceItem
from app.core.database import get_db

router = APIRouter(
    prefix="/outsource",
    tags=["outsource"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[dict])
async def read_outsource_items(db: Any = Depends(get_db)):
    items = [i for i in db.query(OutsourceItem).all() if not getattr(i, 'is_deleted', False)]
    return [{
        "id": str(i.id),
        "task_id": str(i.task_id) if i.task_id else None,
        "title": i.title or "",
        "vendor": i.vendor or "",
        "status": i.status or "Pending",
        "cost": i.cost or 0,
        "expected_date": str(i.expected_date) if i.expected_date else None,
        "dc_generated": i.dc_generated if i.dc_generated is not None else False,
        "transport_status": i.transport_status or "Not Started",
        "follow_up_time": str(i.follow_up_time) if i.follow_up_time else None,
        "pickup_status": i.pickup_status or "Pending",
        "updated_at": str(i.updated_at) if i.updated_at else None,
    } for i in items]

@router.post("", response_model=dict)
async def create_outsource_item(item: OutsourceCreate, db: Any = Depends(get_db)):
    new_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    new_item_data = {
        "id": new_id,
        "task_id": item.task_id,
        "title": item.title,
        "vendor": item.vendor,
        "status": item.status,
        "cost": item.cost,
        "expected_date": item.expected_date,
        "dc_generated": item.dc_generated,
        "transport_status": item.transport_status,
        "follow_up_time": item.follow_up_time.isoformat() if item.follow_up_time else None,
        "pickup_status": item.pickup_status,
        "updated_at": now,
        "is_deleted": False
    }
    new_item = OutsourceItem(**new_item_data)
    db.add(new_item)
    db.commit()
    return new_item_data

@router.put("/{item_id}", response_model=dict)
async def update_outsource_item(item_id: str, item_update: OutsourceUpdate, db: Any = Depends(get_db)):
    db_item = db.query(OutsourceItem).filter(id=item_id).first()
    if not db_item or getattr(db_item, 'is_deleted', False):
        raise HTTPException(status_code=404, detail="Item not found")
    
    up_data = item_update.dict(exclude_unset=True)
    for k, v in up_data.items():
        if k == 'follow_up_time' and v:
            setattr(db_item, k, v.isoformat())
        else:
            setattr(db_item, k, v)
    
    db_item.updated_at = datetime.now().isoformat()
    db.commit()
    
    return {
        "id": str(db_item.id),
        "task_id": str(db_item.task_id),
        "title": getattr(db_item, 'title', ''),
        "vendor": getattr(db_item, 'vendor', ''),
        "status": getattr(db_item, 'status', ''),
        "cost": getattr(db_item, 'cost', 0),
        "expected_date": str(getattr(db_item, 'expected_date', '')),
        "dc_generated": getattr(db_item, 'dc_generated', False),
        "transport_status": getattr(db_item, 'transport_status', ''),
        "follow_up_time": str(getattr(db_item, 'follow_up_time', '')),
        "pickup_status": getattr(db_item, 'pickup_status', ''),
        "updated_at": str(db_item.updated_at),
    }

@router.delete("/{item_id}")
async def delete_outsource_item(item_id: str, db: Any = Depends(get_db)):
    db_item = db.query(OutsourceItem).filter(id=item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db_item.is_deleted = True
    db_item.updated_at = datetime.now().isoformat()
    db.commit()
    return {"message": "Item deleted successfully"}
