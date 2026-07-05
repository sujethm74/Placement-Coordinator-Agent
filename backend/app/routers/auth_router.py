from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db
from ..crud_helpers import set_student_skills

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user. If role=student, also creates a linked student profile."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    student_id = None
    if payload.role == models.UserRole.STUDENT:
        student = models.Student(
            user_id=user.id,
            name=payload.name or payload.email.split("@")[0],
            email=payload.email,
            phone=None,
            cgpa=payload.cgpa or 0.0,
            branch=payload.branch,
        )
        db.add(student)
        db.flush()
        set_student_skills(db, student, payload.skills or [])
        student_id = student.id

    db.commit()

    token = auth.create_access_token({"sub": str(user.id), "role": user.role.value})
    return schemas.Token(access_token=token, role=user.role, user_id=user.id, student_id=student_id)


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    student_id = user.student.id if user.student else None
    token = auth.create_access_token({"sub": str(user.id), "role": user.role.value})
    return schemas.Token(access_token=token, role=user.role, user_id=user.id, student_id=student_id)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
