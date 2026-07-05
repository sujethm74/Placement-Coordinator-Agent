from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth
from ..database import get_db
from ..crud_helpers import set_student_skills, student_to_out

router = APIRouter(prefix="/students", tags=["Students"])


def _query_base(db: Session):
    return db.query(models.Student).options(joinedload(models.Student.skills).joinedload(models.StudentSkill.skill))


@router.get("", response_model=List[schemas.StudentOut])
def list_students(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name or email"),
    branch: Optional[str] = Query(None),
    min_cgpa: Optional[float] = Query(None),
    skill: Optional[str] = Query(None, description="Filter by a skill name"),
    current_user: models.User = Depends(auth.get_current_user),
):
    q = _query_base(db)
    if search:
        like = f"%{search}%"
        q = q.filter((models.Student.name.ilike(like)) | (models.Student.email.ilike(like)))
    if branch:
        q = q.filter(models.Student.branch.ilike(branch))
    if min_cgpa is not None:
        q = q.filter(models.Student.cgpa >= min_cgpa)
    students = q.all()
    if skill:
        skill_lower = skill.strip().lower()
        students = [s for s in students if skill_lower in {sk.skill.name.lower() for sk in s.skills}]
    return [student_to_out(s) for s in students]


@router.get("/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    student = _query_base(db).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_to_out(student)


@router.post("", response_model=schemas.StudentOut, status_code=201)
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    existing = db.query(models.Student).filter(models.Student.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A student with this email already exists")
    student = models.Student(
        name=payload.name, email=payload.email, phone=payload.phone,
        cgpa=payload.cgpa, branch=payload.branch, resume_link=payload.resume_link,
    )
    db.add(student)
    db.flush()
    set_student_skills(db, student, payload.skills)
    db.commit()
    db.refresh(student)
    return student_to_out(student)


@router.put("/{student_id}", response_model=schemas.StudentOut)
def update_student(student_id: int, payload: schemas.StudentUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    data = payload.model_dump(exclude_unset=True)
    skills = data.pop("skills", None)
    for key, value in data.items():
        setattr(student, key, value)
    if skills is not None:
        set_student_skills(db, student, skills)
    db.commit()
    db.refresh(student)
    return student_to_out(student)


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_admin)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return None
