"""
Core scoring / matching logic shared across the Eligibility Engine,
Recommendation System, Skill Gap Analyzer, Chatbot and Leaderboard.

This is intentionally simple, transparent, rule-based logic (no external
paid AI APIs), as requested. It is isolated here so every feature that
needs "how good is this student for this job" uses the exact same formula.

score = (skill_match_pct * SKILL_WEIGHT)
      + (cgpa_normalized * CGPA_WEIGHT)
      + (past_performance_normalized * PAST_PERFORMANCE_WEIGHT)
"""
from typing import Iterable, List, Set

from . import models

SKILL_WEIGHT = 0.6
CGPA_WEIGHT = 0.25
PAST_PERFORMANCE_WEIGHT = 0.15

MAX_CGPA = 10.0
MAX_PAST_OFFERS_CONSIDERED = 3  # more than this gives no extra benefit


def normalize_skill(name: str) -> str:
    return name.strip().lower()


def student_skill_set(student: models.Student) -> Set[str]:
    return {normalize_skill(s.skill.name) for s in student.skills}


def company_skill_set(company: models.Company) -> Set[str]:
    return {normalize_skill(cs.skill.name) for cs in company.required_skills}


def skill_match_pct(student_skills: Set[str], required_skills: Set[str]) -> float:
    """Percentage of the job's required skills the student possesses."""
    if not required_skills:
        return 100.0
    matched = student_skills & required_skills
    return round(100.0 * len(matched) / len(required_skills), 2)


def compute_score(student: models.Student, company: models.Company) -> dict:
    s_skills = student_skill_set(student)
    c_skills = company_skill_set(company)
    matched = s_skills & c_skills
    match_pct = skill_match_pct(s_skills, c_skills)

    cgpa_norm = min(student.cgpa / MAX_CGPA, 1.0) * 100
    past_perf_norm = min((student.past_offers or 0) / MAX_PAST_OFFERS_CONSIDERED, 1.0) * 100

    total = (
        (match_pct * SKILL_WEIGHT)
        + (cgpa_norm * CGPA_WEIGHT)
        + (past_perf_norm * PAST_PERFORMANCE_WEIGHT)
    )
    return {
        "matched_skills": sorted(matched),
        "skill_match_pct": match_pct,
        "score": round(total, 2),
    }


def is_eligible(student: models.Student, company: models.Company) -> bool:
    """A student is eligible if CGPA meets the minimum, their branch matches
    the company's eligible branches (if specified), and they have at least
    one of the required skills (or the job requires no specific skills)."""
    if student.cgpa < company.min_cgpa:
        return False
    if company.eligible_branches:
        allowed = {b.strip().upper() for b in company.eligible_branches.split(",") if b.strip()}
        if allowed and (not student.branch or student.branch.upper() not in allowed):
            return False
    c_skills = company_skill_set(company)
    if not c_skills:
        return True
    s_skills = student_skill_set(student)
    return len(s_skills & c_skills) > 0


COMMON_SKILLS_KEYWORDS = [
    "python", "java", "c++", "c", "javascript", "typescript", "react", "angular",
    "vue", "node.js", "node", "express", "django", "flask", "fastapi", "spring",
    "sql", "mysql", "postgresql", "mongodb", "aws", "azure", "gcp", "docker",
    "kubernetes", "git", "html", "css", "tailwind", "machine learning", "deep learning",
    "data structures", "algorithms", "dsa", "pandas", "numpy", "tensorflow", "pytorch",
    "rest api", "graphql", "linux", "excel", "power bi", "tableau",
    "leadership", "problem solving", "agile", "scrum", "ci/cd", "testing", "selenium",
]

ROLE_SKILL_MAP = {
    "Software Development Engineer": {"python", "java", "c++", "data structures", "algorithms", "dsa", "git"},
    "Full Stack Developer": {"javascript", "react", "node.js", "node", "html", "css", "sql", "express"},
    "Backend Developer": {"python", "django", "flask", "fastapi", "sql", "mongodb", "rest api"},
    "Frontend Developer": {"html", "css", "javascript", "react", "angular", "vue", "tailwind"},
    "Data Analyst": {"sql", "excel", "power bi", "tableau", "pandas", "numpy"},
    "Data Scientist / ML Engineer": {"python", "machine learning", "deep learning", "pandas", "numpy", "tensorflow", "pytorch"},
    "DevOps Engineer": {"docker", "kubernetes", "aws", "azure", "gcp", "linux", "ci/cd"},
    "QA / Test Engineer": {"testing", "selenium", "python", "java"},
}


def extract_skills_from_text(text: str) -> List[str]:
    """Keyword-matching skill extractor for the Resume Analyzer.

    Uses word-boundary regex matching (rather than naive substring search)
    so short keywords like "c" or "r" don't false-positive inside unrelated
    words (e.g. "c" inside "django").
    """
    import re
    text_lower = text.lower()
    found = []
    for kw in COMMON_SKILLS_KEYWORDS:
        pattern = r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.append(kw)
    return sorted(set(found))


def suggest_roles_from_skills(skills: Iterable[str]) -> List[str]:
    skill_set = {normalize_skill(s) for s in skills}
    suggestions = []
    for role, role_skills in ROLE_SKILL_MAP.items():
        overlap = skill_set & role_skills
        if overlap:
            pct = len(overlap) / len(role_skills)
            suggestions.append((role, pct))
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return [role for role, _ in suggestions[:5]] or ["General Software Trainee"]
