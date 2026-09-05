"""
Batch Processing API
"""
import uuid
from fastapi import APIRouter, Depends, Body, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.business import BatchRun
from app.schemas.base import BaseResponse
from app.workers.batch_processor import run_batch_processing

router = APIRouter()


@router.post("/run")
def run_batch(
    target_count: int = Body(default=500, embed=True),
    db: Session = Depends(get_db),
):
    """
    Run batch processing of synthetic cases.
    Generates target_count cases and runs full recovery workflow on all.
    Returns comprehensive metrics.
    """
    if target_count < 1:
        return BaseResponse(success=False, error="target_count must be at least 1")
    if target_count > 1000:
        target_count = 1000

    metrics = run_batch_processing(db, target_count)
    return BaseResponse(success=True, data=metrics)


@router.get("/")
def list_batches(db: Session = Depends(get_db)):
    """List all batch runs."""
    batches = db.query(BatchRun).order_by(BatchRun.created_at.desc()).limit(20).all()
    return BaseResponse(success=True, data=[{
        "batch_id": b.batch_id,
        "status": b.status,
        "total_cases": b.total_cases,
        "processed_cases": b.processed_cases,
        "total_recovered": b.total_recovered,
        "recovery_rate": b.recovery_rate,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "completed_at": b.completed_at.isoformat() if b.completed_at else None,
    } for b in batches])


@router.get("/{batch_id}/results")
def get_batch_results(batch_id: str, db: Session = Depends(get_db)):
    """Get results of a specific batch run."""
    batch = db.query(BatchRun).filter(BatchRun.batch_id == batch_id).first()
    if not batch:
        return BaseResponse(success=False, error="Batch not found")
    
    return BaseResponse(success=True, data={
        "batch_id": batch.batch_id,
        "status": batch.status,
        "total_cases": batch.total_cases,
        "processed_cases": batch.processed_cases,
        "total_revenue_at_risk": batch.total_revenue_at_risk,
        "total_recovered": batch.total_recovered,
        "recovery_rate": batch.recovery_rate,
        "cases_recovered": batch.cases_recovered,
        "cases_failed": batch.cases_failed,
        "cases_blocked": batch.cases_blocked,
        "cases_escalated": batch.cases_escalated,
        "cases_stopped": batch.cases_stopped,
        "actions_executed": batch.actions_executed,
        "actions_blocked": batch.actions_blocked,
        "human_escalations": batch.human_escalations,
        "breakdown_by_type": batch.breakdown_by_type,
        "started_at": batch.started_at.isoformat() if batch.started_at else None,
        "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
    })
