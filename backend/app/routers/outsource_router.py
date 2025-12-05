from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.outsource_model import OutsourceCreate, OutsourceUpdate
from app.models.models_db import OutsourceItem
from app.core.database import get_db
import uuid

router = APIRouter(
    prefix="/outsource",
    tags=["outsource"],
    responses={404: {"description": "Not found"}},
)

# ----------------------------------------------------------------------
# GET ALL OUTSOURCE ITEMS
# ----------------------------------------------------------------------
@router.get("/", response_model=List[dict])
async def read_outsource_items(db: Session = Depends(get_db)):
    items = db.query(OutsourceItem).all()
    return [
        {
            "id": i.id,
            "task_id": i.task_id,
            "title": i.title,
            "vendor": i.vendor,
            "status": i.status,
            "cost": i.cost,
            "expected_date": i.expected_date,
            "dc_generated": i.dc_generated,
            "transport_status": i.transport_status,
            "follow_up_time": i.follow_up_time.isoformat() if i.follow_up_time else None,
            "pickup_status": i.pickup_status,
            "updated_at": i.updated_at.isoformat() if i.updated_at else None,
        }
        for i in items
    ]

# ----------------------------------------------------------------------
# CREATE OUTSOURCE ITEM
# ----------------------------------------------------------------------
@router.post("/", response_model=dict)
async def create_outsource_item(item: OutsourceCreate, db: Session = Depends(get_db)):
    new_item = OutsourceItem(
        id=str(uuid.uuid4()),
        task_id=item.task_id,
        title=item.title,
        vendor=item.vendor,
        status=item.status,
        cost=item.cost,
        expected_date=item.expected_date,
        dc_generated=item.dc_generated,
        transport_status=item.transport_status,
        follow_up_time=item.follow_up_time,
        pickup_status=item.pickup_status,
        updated_at=datetime.utcnow(),
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return {
        "id": new_item.id,
        "task_id": new_item.task_id,
        "title": new_item.title,
        "vendor": new_item.vendor,
        "status": new_item.status,
        "cost": new_item.cost,
        "expected_date": new_item.expected_date,
        "dc_generated": new_item.dc_generated,
        "transport_status": new_item.transport_status,
        "follow_up_time": new_item.follow_up_time.isoformat() if new_item.follow_up_time else None,
        "pickup_status": new_item.pickup_status,
        "updated_at": new_item.updated_at.isoformat(),
    }

# ----------------------------------------------------------------------
# UPDATE OUTSOURCE ITEM
# ----------------------------------------------------------------------
@router.put("/{item_id}", response_model=dict)
async def update_outsource_item(item_id: str, item_update: OutsourceUpdate, db: Session = Depends(get_db)):
    db_item = db.query(OutsourceItem).filter(OutsourceItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    # Always bump the updated_at timestamp
    db_item.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_item)
    
    return {
        "id": db_item.id,
        "task_id": db_item.task_id,
        "title": db_item.title,
        "vendor": db_item.vendor,
        "status": db_item.status,
        "cost": db_item.cost,
        "expected_date": db_item.expected_date,
        "dc_generated": db_item.dc_generated,
        "transport_status": db_item.transport_status,
        "follow_up_time": db_item.follow_up_time.isoformat() if db_item.follow_up_time else None,
        "pickup_status": db_item.pickup_status,
        "updated_at": db_item.updated_at.isoformat(),
    }

# ----------------------------------------------------------------------
# DELETE OUTSOURCE ITEM
# ----------------------------------------------------------------------
@router.delete("/{item_id}")
async def delete_outsource_item(item_id: str, db: Session = Depends(get_db)):
    db_item = db.query(OutsourceItem).filter(OutsourceItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}
