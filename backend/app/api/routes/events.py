from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.base import EventCreate, BaseResponse
from app.services.ingestion import process_event

router = APIRouter()

@router.post("/", response_model=BaseResponse[dict])
def ingest_event(payload: EventCreate, db: Session = Depends(get_db)):
    try:
        result = process_event(db, payload)
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, error=str(e))
