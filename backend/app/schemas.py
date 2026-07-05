from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from .models import UserRole, ApplicationStatus, InterviewMode

VALID_BRANCHES = {"CSE", "IT", "ECE", "EE", "ME", "CE", "MCA", "BCA", "AIDS"}

def check_branch(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    val = v.strip().upper()
    if val not in VALID_BRANCHES:
        raise ValueError(f"Branch must be one of: {', '.join(sorted(VALID_BRANCHES))}")
    return val


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.STUDENT
    # optional student profile fields, used only when role == student
    name: Optional[str] = None
    phone: Optional[str] = None
    cgpa: Optional[float] = 0.0
    branch: Optional[str] = None
    skills: Optional[List[str]] = []

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        return check_branch(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: int
    student_id: Optional[int] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    role: UserRole


# ---------- Students ----------
class StudentBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    cgpa: float = 0.0
    branch: Optional[str] = None
    resume_link: Optional[str] = None
    skills: List[str] = []

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        return check_branch(v)


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    cgpa: Optional[float] = None
    branch: Optional[str] = None
    resume_link: Optional[str] = None
    skills: Optional[List[str]] = None

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        return check_branch(v)


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    past_offers: int = 0


# ---------- Companies ----------
class CompanyBase(BaseModel):
    name: str
    role: str
    package_lpa: float
    min_cgpa: float
    deadline: datetime
    description: Optional[str] = None
    required_skills: List[str] = []
    eligible_branches: Optional[List[str]] = []


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    package_lpa: Optional[float] = None
    min_cgpa: Optional[float] = None
    deadline: Optional[datetime] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    eligible_branches: Optional[List[str]] = None


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Applications ----------
class ApplicationCreate(BaseModel):
    student_id: int
    company_id: int


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    company_id: int
    status: ApplicationStatus
    applied_at: datetime
    student_name: Optional[str] = None
    company_name: Optional[str] = None


# ---------- Interviews ----------
class InterviewCreate(BaseModel):
    application_id: int
    scheduled_at: datetime
    mode: InterviewMode = InterviewMode.ONLINE
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    company_id: int
    scheduled_at: datetime
    mode: InterviewMode
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


# ---------- Eligibility / Recommendations ----------
class EligibleStudent(BaseModel):
    student_id: int
    name: str
    cgpa: float
    matched_skills: List[str]
    skill_match_pct: float
    score: float


class RecommendedJob(BaseModel):
    company_id: int
    company_name: str
    role: str
    package_lpa: float
    skill_match_pct: float
    score: float


class SkillGapResult(BaseModel):
    company_id: int
    company_name: str
    required_skills: List[str]
    student_skills: List[str]
    missing_skills: List[str]


# ---------- Chatbot ----------
class ChatQuery(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    data: Optional[list] = None


# ---------- Resume Analyzer ----------
class ResumeInput(BaseModel):
    resume_text: str


class MatchedJob(BaseModel):
    company_id: int
    company_name: str
    role: str
    package_lpa: float
    skill_match_pct: float
    score: float


class ResumeAnalysis(BaseModel):
    extracted_skills: List[str]
    suggested_roles: List[str]
    matched_jobs: List[MatchedJob] = []


# ---------- Dashboard ----------
class CompanyHiringStat(BaseModel):
    company_name: str
    selected_count: int
    applied_count: int


class DashboardStats(BaseModel):
    total_students: int
    total_companies: int
    total_placed_students: int
    placement_rate_pct: float
    average_package_lpa: float
    total_applications: int
    company_wise_hiring: List[CompanyHiringStat]
