"""
Relational schema for the Placement Coordinator Agent.

Tables:
    users        - login credentials + role (admin / student)
    students     - student profile, linked 1:1 to a user
    skills       - normalized skill list
    student_skills - many-to-many join (student <-> skill) with proficiency
    companies    - company + job role postings
    company_skills - many-to-many join (company requirement <-> skill)
    applications - student -> company applications with status history
    interviews   - scheduled interviews tied to an application
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text,
    Boolean, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "Applied"
    SHORTLISTED = "Shortlisted"
    REJECTED = "Rejected"
    SELECTED = "Selected"


class InterviewMode(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    student = relationship("Student", back_populates="skills")
    skill = relationship("Skill")

    __table_args__ = (UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    cgpa = Column(Float, nullable=False, default=0.0)
    branch = Column(String, index=True, nullable=True)
    resume_link = Column(String, nullable=True)
    past_offers = Column(Integer, default=0)  # used as a "past performance" signal
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="student")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_students_cgpa", "cgpa"),
    )


class CompanySkill(Base):
    __tablename__ = "company_skills"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", back_populates="required_skills")
    skill = relationship("Skill")

    __table_args__ = (UniqueConstraint("company_id", "skill_id", name="uq_company_skill"),)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    package_lpa = Column(Float, nullable=False, default=0.0)  # salary package, in LPA
    min_cgpa = Column(Float, nullable=False, default=0.0)
    deadline = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    eligible_branches = Column(String, nullable=True)  # Comma-separated list (e.g. "CSE, IT")
    created_at = Column(DateTime, default=datetime.utcnow)

    required_skills = relationship("CompanySkill", back_populates="company", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="company", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="company", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="applications")
    company = relationship("Company", back_populates="applications")
    interview = relationship("Interview", back_populates="application", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("student_id", "company_id", name="uq_student_company_application"),
        Index("ix_applications_status", "status"),
    )


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    mode = Column(Enum(InterviewMode), default=InterviewMode.ONLINE)
    meeting_link = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    application = relationship("Application", back_populates="interview")
    company = relationship("Company", back_populates="interviews")
