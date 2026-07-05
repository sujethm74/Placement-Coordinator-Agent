from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db
from ..notifications import notify, get_notifications

router = APIRouter(tags=["Interviews & Notifications"])


def _to_out(interview: models.Interview) -> dict:
    return {
        "id": interview.id,
        "application_id": interview.application_id,
        "company_id": interview.company_id,
        "scheduled_at": interview.scheduled_at,
        "mode": interview.mode,
        "meeting_link": interview.meeting_link,
        "notes": interview.notes,
    }


@router.get("/interviews", response_model=List[schemas.InterviewOut])
def list_interviews(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return [_to_out(i) for i in db.query(models.Interview).all()]


@router.post("/interviews", response_model=schemas.InterviewOut, status_code=201)
def schedule_interview(payload: schemas.InterviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    application = db.query(models.Application).filter(models.Application.id == payload.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    existing = db.query(models.Interview).filter(models.Interview.application_id == payload.application_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Interview already scheduled for this application")

    interview = models.Interview(
        application_id=payload.application_id,
        company_id=application.company_id,
        scheduled_at=payload.scheduled_at,
        mode=payload.mode,
        meeting_link=payload.meeting_link,
        notes=payload.notes,
    )
    db.add(interview)
    application.status = models.ApplicationStatus.SHORTLISTED
    db.commit()
    db.refresh(interview)

    notify(
        f"Interview scheduled: {application.student.name} with {application.company.name} on "
        f"{payload.scheduled_at.strftime('%Y-%m-%d %H:%M')} ({payload.mode.value}).",
        category="interview",
    )
    return _to_out(interview)


@router.delete("/interviews/{interview_id}", status_code=204)
def cancel_interview(interview_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    db.delete(interview)
    db.commit()
    return None


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Returns recent notifications plus freshly computed alerts for:
      - Company application deadlines within the next 3 days
      - Interviews scheduled within the next 3 days
    """
    now = datetime.utcnow()
    soon = now + timedelta(days=3)

    alerts = []
    upcoming_deadlines = (
        db.query(models.Company)
        .filter(models.Company.deadline >= now, models.Company.deadline <= soon)
        .all()
    )
    for c in upcoming_deadlines:
        alerts.append({
            "message": f"Deadline approaching: {c.name} ({c.role}) closes on {c.deadline.strftime('%Y-%m-%d')}.",
            "category": "deadline",
            "timestamp": now.isoformat(),
        })

    upcoming_interviews = (
        db.query(models.Interview)
        .filter(models.Interview.scheduled_at >= now, models.Interview.scheduled_at <= soon)
        .all()
    )
    for iv in upcoming_interviews:
        alerts.append({
            "message": f"Interview reminder: {iv.application.student.name} — {iv.application.company.name} on "
                       f"{iv.scheduled_at.strftime('%Y-%m-%d %H:%M')}.",
            "category": "interview",
            "timestamp": now.isoformat(),
        })

    return {"live_alerts": alerts, "recent_activity": get_notifications()}
