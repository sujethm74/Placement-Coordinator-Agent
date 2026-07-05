from typing import Iterable, List
from sqlalchemy.orm import Session

from . import models


def get_or_create_skill(db: Session, name: str) -> models.Skill:
    clean = name.strip()
    skill = db.query(models.Skill).filter(models.Skill.name.ilike(clean)).first()
    if skill:
        return skill
    skill = models.Skill(name=clean)
    db.add(skill)
    db.flush()
    return skill


def set_student_skills(db: Session, student: models.Student, skill_names: Iterable[str]):
    current_skills_map = {s.skill.name.lower(): s for s in student.skills if s.skill}
    new_names = {name.strip().lower() for name in skill_names if name.strip()}
    
    # Remove skills no longer present
    for name, student_skill in list(current_skills_map.items()):
        if name not in new_names:
            student.skills.remove(student_skill)
            
    # Add new skills
    for name in new_names:
        if name not in current_skills_map:
            skill = get_or_create_skill(db, name)
            student.skills.append(models.StudentSkill(student_id=student.id, skill_id=skill.id))


def set_company_skills(db: Session, company: models.Company, skill_names: Iterable[str]):
    current_skills_map = {cs.skill.name.lower(): cs for cs in company.required_skills if cs.skill}
    new_names = {name.strip().lower() for name in skill_names if name.strip()}
    
    # Remove requirements no longer present
    for name, company_skill in list(current_skills_map.items()):
        if name not in new_names:
            company.required_skills.remove(company_skill)
            
    # Add new requirements
    for name in new_names:
        if name not in current_skills_map:
            skill = get_or_create_skill(db, name)
            company.required_skills.append(models.CompanySkill(company_id=company.id, skill_id=skill.id))


def student_to_out(student: models.Student) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "cgpa": student.cgpa,
        "branch": student.branch,
        "resume_link": student.resume_link,
        "past_offers": student.past_offers,
        "skills": [s.skill.name for s in student.skills],
    }


def company_to_out(company: models.Company) -> dict:
    branches = []
    if company.eligible_branches:
        branches = [b.strip() for b in company.eligible_branches.split(",") if b.strip()]
    return {
        "id": company.id,
        "name": company.name,
        "role": company.role,
        "package_lpa": company.package_lpa,
        "min_cgpa": company.min_cgpa,
        "deadline": company.deadline,
        "description": company.description,
        "required_skills": [cs.skill.name for cs in company.required_skills],
        "eligible_branches": branches,
    }
