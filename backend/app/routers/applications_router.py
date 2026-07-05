from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth
from ..database import get_db
from ..notifications import notify

router = APIRouter(prefix="/applications", tags=["Applications"])


def _to_out(app_: models.Application) -> dict:
    return {
        "id": app_.id,
        "student_id": app_.student_id,
        "company_id": app_.company_id,
        "status": app_.status,
        "applied_at": app_.applied_at,
        "student_name": app_.student.name if app_.student else None,
        "company_name": app_.company.name if app_.company else None,
    }


@router.get("", response_model=List[schemas.ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    student_id: Optional[int] = Query(None),
    company_id: Optional[int] = Query(None),
    status_filter: Optional[models.ApplicationStatus] = Query(None, alias="status"),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = db.query(models.Application).options(
        joinedload(models.Application.student), joinedload(models.Application.company)
    )
    if student_id:
        q = q.filter(models.Application.student_id == student_id)
    if company_id:
        q = q.filter(models.Application.company_id == company_id)
    if status_filter:
        q = q.filter(models.Application.status == status_filter)
    return [_to_out(a) for a in q.order_by(models.Application.applied_at.desc()).all()]


@router.post("", response_model=schemas.ApplicationOut, status_code=201)
def apply_to_company(payload: schemas.ApplicationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    company = db.query(models.Company).filter(models.Company.id == payload.company_id).first()
    if not student or not company:
        raise HTTPException(status_code=404, detail="Student or company not found")

    duplicate = (
        db.query(models.Application)
        .filter(models.Application.student_id == payload.student_id, models.Application.company_id == payload.company_id)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Student has already applied to this company")

    application = models.Application(student_id=payload.student_id, company_id=payload.company_id)
    db.add(application)
    db.commit()
    db.refresh(application)

    notify(
        f"New application: {student.name} applied to {company.name} ({company.role})."
    )
    return _to_out(application)


@router.patch("/{application_id}/status", response_model=schemas.ApplicationOut)
def update_status(application_id: int, payload: schemas.ApplicationStatusUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = payload.status
    if payload.status == models.ApplicationStatus.SELECTED:
        application.student.past_offers = (application.student.past_offers or 0) + 1
    db.commit()
    db.refresh(application)

    notify(
        f"Status update: {application.student.name}'s application to {application.company.name} is now '{application.status.value}'."
    )
    return _to_out(application)


@router.delete("/{application_id}", status_code=204)
def withdraw_application(application_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()
    return None
