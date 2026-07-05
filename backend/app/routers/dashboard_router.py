from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["Analytics Dashboard"])


@router.get("", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    total_students = db.query(func.count(models.Student.id)).scalar() or 0
    total_companies = db.query(func.count(models.Company.id)).scalar() or 0
    total_applications = db.query(func.count(models.Application.id)).scalar() or 0

    placed_student_ids = (
        db.query(models.Application.student_id)
        .filter(models.Application.status == models.ApplicationStatus.SELECTED)
        .distinct()
        .all()
    )
    total_placed = len(placed_student_ids)
    placement_rate = round((total_placed / total_students) * 100, 2) if total_students else 0.0

    avg_package = (
        db.query(func.avg(models.Company.package_lpa))
        .join(models.Application, models.Application.company_id == models.Company.id)
        .filter(models.Application.status == models.ApplicationStatus.SELECTED)
        .scalar()
    )
    avg_package = round(avg_package, 2) if avg_package else 0.0

    company_stats = []
    companies = db.query(models.Company).all()
    for c in companies:
        applied_count = db.query(func.count(models.Application.id)).filter(models.Application.company_id == c.id).scalar() or 0
        selected_count = (
            db.query(func.count(models.Application.id))
            .filter(models.Application.company_id == c.id, models.Application.status == models.ApplicationStatus.SELECTED)
            .scalar() or 0
        )
        if applied_count > 0:
            company_stats.append(schemas.CompanyHiringStat(
                company_name=c.name, selected_count=selected_count, applied_count=applied_count
            ))

    return schemas.DashboardStats(
        total_students=total_students,
        total_companies=total_companies,
        total_placed_students=total_placed,
        placement_rate_pct=placement_rate,
        average_package_lpa=avg_package,
        total_applications=total_applications,
        company_wise_hiring=company_stats,
    )
