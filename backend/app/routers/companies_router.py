from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth
from ..database import get_db
from ..crud_helpers import set_company_skills, company_to_out

router = APIRouter(prefix="/companies", tags=["Companies"])


def _query_base(db: Session):
    return db.query(models.Company).options(joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill))


@router.get("", response_model=List[schemas.CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = _query_base(db)
    if search:
        like = f"%{search}%"
        q = q.filter((models.Company.name.ilike(like)) | (models.Company.role.ilike(like)))
    return [company_to_out(c) for c in q.all()]


@router.get("/{company_id}", response_model=schemas.CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    company = _query_base(db).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company_to_out(company)


@router.post("", response_model=schemas.CompanyOut, status_code=201)
def create_company(payload: schemas.CompanyCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    branches_str = ",".join(payload.eligible_branches) if payload.eligible_branches else None
    company = models.Company(
        name=payload.name, role=payload.role, package_lpa=payload.package_lpa,
        min_cgpa=payload.min_cgpa, deadline=payload.deadline, description=payload.description,
        eligible_branches=branches_str
    )
    db.add(company)
    db.flush()
    set_company_skills(db, company, payload.required_skills)
    db.commit()
    db.refresh(company)
    return company_to_out(company)


@router.put("/{company_id}", response_model=schemas.CompanyOut)
def update_company(company_id: int, payload: schemas.CompanyUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    data = payload.model_dump(exclude_unset=True)
    skills = data.pop("required_skills", None)
    branches = data.pop("eligible_branches", None)
    for key, value in data.items():
        setattr(company, key, value)
    if branches is not None:
        company.eligible_branches = ",".join(branches) if branches else None
    if skills is not None:
        set_company_skills(db, company, skills)
    db.commit()
    db.refresh(company)
    return company_to_out(company)


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return None
