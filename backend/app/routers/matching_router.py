from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth, scoring
from ..database import get_db

router = APIRouter(tags=["Eligibility & Recommendations"])


def _load_students(db: Session):
    return db.query(models.Student).options(
        joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
    ).all()


def _load_companies(db: Session):
    return db.query(models.Company).options(
        joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
    ).all()


@router.get("/eligibility/{company_id}", response_model=List[schemas.EligibleStudent])
def eligible_students_for_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Returns every eligible student for a company, ranked by score (desc)."""
    company = db.query(models.Company).options(
        joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
    ).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    results = []
    for student in _load_students(db):
        if scoring.is_eligible(student, company):
            details = scoring.compute_score(student, company)
            results.append(schemas.EligibleStudent(
                student_id=student.id,
                name=student.name,
                cgpa=student.cgpa,
                matched_skills=details["matched_skills"],
                skill_match_pct=details["skill_match_pct"],
                score=details["score"],
            ))
    results.sort(key=lambda r: r.score, reverse=True)
    return results


@router.get("/recommendations/students-for-job/{company_id}", response_model=List[schemas.EligibleStudent])
def recommend_students_for_job(
    company_id: int,
    top_n: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Same ranking as eligibility, but not restricted to only 'eligible' students —
    it returns the best overall matches (top_n), useful for a coordinator scanning talent."""
    company = db.query(models.Company).options(
        joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
    ).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    results = []
    for student in _load_students(db):
        details = scoring.compute_score(student, company)
        results.append(schemas.EligibleStudent(
            student_id=student.id,
            name=student.name,
            cgpa=student.cgpa,
            matched_skills=details["matched_skills"],
            skill_match_pct=details["skill_match_pct"],
            score=details["score"],
        ))
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]


@router.get("/recommendations/jobs-for-student/{student_id}", response_model=List[schemas.RecommendedJob])
def recommend_jobs_for_student(
    student_id: int,
    top_n: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    student = db.query(models.Student).options(
        joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
    ).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    results = []
    for company in _load_companies(db):
        details = scoring.compute_score(student, company)
        results.append(schemas.RecommendedJob(
            company_id=company.id,
            company_name=company.name,
            role=company.role,
            package_lpa=company.package_lpa,
            skill_match_pct=details["skill_match_pct"],
            score=details["score"],
        ))
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_n]


@router.get("/skill-gap/{student_id}/{company_id}", response_model=schemas.SkillGapResult)
def skill_gap(
    student_id: int,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    student = db.query(models.Student).options(
        joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
    ).filter(models.Student.id == student_id).first()
    company = db.query(models.Company).options(
        joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
    ).filter(models.Company.id == company_id).first()
    if not student or not company:
        raise HTTPException(status_code=404, detail="Student or company not found")

    student_skills = scoring.student_skill_set(student)
    required = scoring.company_skill_set(company)
    missing = sorted(required - student_skills)

    return schemas.SkillGapResult(
        company_id=company.id,
        company_name=company.name,
        required_skills=sorted(required),
        student_skills=sorted(student_skills),
        missing_skills=missing,
    )


@router.get("/leaderboard", response_model=List[schemas.StudentOut])
def leaderboard(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    Ranks students by a composite of CGPA, number of distinct skills, and
    past placement/selection history (past_offers). Highest first.
    """
    students = _load_students(db)

    def rank_key(s: models.Student):
        cgpa_norm = min(s.cgpa / scoring.MAX_CGPA, 1.0) * 100
        skill_bonus = min(len(s.skills), 10) * 2  # up to +20
        offer_bonus = (s.past_offers or 0) * 15
        return cgpa_norm + skill_bonus + offer_bonus

    ranked = sorted(students, key=rank_key, reverse=True)
    from ..crud_helpers import student_to_out
    return [student_to_out(s) for s in ranked]
