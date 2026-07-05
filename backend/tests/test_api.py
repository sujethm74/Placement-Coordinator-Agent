"""
Basic tests for the Placement Coordinator Agent API.
Run with: pytest -v  (from the backend/ directory)

Uses a separate SQLite test database so it never touches placement.db.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_placement.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_admin_token():
    client.post("/auth/register", json={
        "email": "admin@test.com", "password": "adminpass", "role": "admin"
    })
    res = client.post("/auth/login", json={"email": "admin@test.com", "password": "adminpass"})
    return res.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    res = client.post("/auth/register", json={
        "email": "student1@test.com", "password": "pass123", "role": "student",
        "name": "Test Student", "cgpa": 8.0, "branch": "CSE", "skills": ["python", "sql"]
    })
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "student"
    assert data["student_id"] is not None

    res2 = client.post("/auth/login", json={"email": "student1@test.com", "password": "pass123"})
    assert res2.status_code == 200


def test_login_wrong_password():
    res = client.post("/auth/login", json={"email": "student1@test.com", "password": "wrong"})
    assert res.status_code == 401


def test_admin_can_create_student_and_company():
    token = get_admin_token()
    headers = auth_headers(token)

    res = client.post("/students", json={
        "name": "Jane Doe", "email": "jane@test.com", "cgpa": 9.0,
        "branch": "IT", "skills": ["java", "sql"]
    }, headers=headers)
    assert res.status_code == 201
    student_id = res.json()["id"]

    res2 = client.post("/companies", json={
        "name": "TestCorp", "role": "SDE", "package_lpa": 10.0, "min_cgpa": 7.0,
        "deadline": "2027-01-01T00:00:00", "required_skills": ["java", "sql"]
    }, headers=headers)
    assert res2.status_code == 201
    company_id = res2.json()["id"]

    # non-admin (unauthenticated) cannot create
    res3 = client.post("/students", json={"name": "X", "email": "x@test.com", "cgpa": 5})
    assert res3.status_code == 401

    return student_id, company_id


def test_application_flow_and_duplicate_prevention():
    token = get_admin_token()
    headers = auth_headers(token)

    student_res = client.post("/students", json={
        "name": "App Student", "email": "appstudent@test.com", "cgpa": 8.5, "skills": ["python"]
    }, headers=headers)
    student_id = student_res.json()["id"]

    company_res = client.post("/companies", json={
        "name": "AppCorp", "role": "Dev", "package_lpa": 8.0, "min_cgpa": 6.0,
        "deadline": "2027-01-01T00:00:00", "required_skills": ["python"]
    }, headers=headers)
    company_id = company_res.json()["id"]

    res = client.post("/applications", json={"student_id": student_id, "company_id": company_id}, headers=headers)
    assert res.status_code == 201

    # Duplicate application should be rejected
    dup = client.post("/applications", json={"student_id": student_id, "company_id": company_id}, headers=headers)
    assert dup.status_code == 409

    # Update status
    app_id = res.json()["id"]
    status_res = client.patch(f"/applications/{app_id}/status", json={"status": "Selected"}, headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "Selected"


def test_eligibility_engine():
    token = get_admin_token()
    headers = auth_headers(token)

    client.post("/students", json={
        "name": "Eligible Kid", "email": "eligible@test.com", "cgpa": 9.0, "skills": ["python", "django"]
    }, headers=headers)
    client.post("/students", json={
        "name": "Ineligible Kid", "email": "ineligible@test.com", "cgpa": 3.0, "skills": ["python"]
    }, headers=headers)
    company_res = client.post("/companies", json={
        "name": "EligCorp", "role": "Backend Dev", "package_lpa": 9.0, "min_cgpa": 7.0,
        "deadline": "2027-01-01T00:00:00", "required_skills": ["python", "django"]
    }, headers=headers)
    company_id = company_res.json()["id"]

    res = client.get(f"/eligibility/{company_id}", headers=headers)
    assert res.status_code == 200
    names = [r["name"] for r in res.json()]
    assert "Eligible Kid" in names
    assert "Ineligible Kid" not in names


def test_resume_analyzer_no_false_positive_single_letter():
    token = get_admin_token()
    headers = auth_headers(token)
    res = client.post("/resume/analyze", json={
        "resume_text": "Experienced in Django and React with strong problem solving skills."
    }, headers=headers)
    assert res.status_code == 200
    skills = res.json()["extracted_skills"]
    assert "c" not in skills  # regression test: "c" must not match inside "django"/"react"
    assert "django" in skills
    assert "react" in skills


def test_chatbot_basic_query():
    token = get_admin_token()
    headers = auth_headers(token)
    client.post("/companies", json={
        "name": "ChatCorp", "role": "SDE", "package_lpa": 10.0, "min_cgpa": 6.0,
        "deadline": "2027-01-01T00:00:00", "required_skills": ["python"]
    }, headers=headers)
    res = client.post("/chatbot/query", json={"query": "Which students are eligible for ChatCorp?"}, headers=headers)
    assert res.status_code == 200
    assert "ChatCorp" in res.json()["answer"]


def test_dashboard_stats():
    token = get_admin_token()
    headers = auth_headers(token)
    res = client.get("/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_students" in data
    assert "placement_rate_pct" in data


def test_invalid_branch_registration():
    res = client.post("/auth/register", json={
        "email": "invalid_branch@test.com", "password": "pass123", "role": "student",
        "name": "Invalid Student", "cgpa": 8.0, "branch": "INVALID_COURSE", "skills": []
    })
    assert res.status_code == 422
    assert "Branch must be one of" in res.text


def test_valid_branch_registration():
    res = client.post("/auth/register", json={
        "email": "valid_branch@test.com", "password": "pass123", "role": "student",
        "name": "Valid Student", "cgpa": 8.0, "branch": "CSE", "skills": []
    })
    assert res.status_code == 201


def test_resume_upload_pdf():
    token = get_admin_token()
    headers = auth_headers(token)
    
    from unittest.mock import patch
    with patch("app.routers.resume_router.extract_text_from_pdf", return_value="Experienced in Python and SQL."):
        files = {"file": ("resume.pdf", b"dummy pdf data", "application/pdf")}
        res = client.post("/resume/analyze", files=files, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "python" in data["extracted_skills"]
        assert "sql" in data["extracted_skills"]
        assert "matched_jobs" in data


def test_resume_upload_docx():
    token = get_admin_token()
    headers = auth_headers(token)
    
    from unittest.mock import patch
    with patch("app.routers.resume_router.extract_text_from_docx", return_value="Experienced in Java and SQL."):
        files = {"file": ("resume.docx", b"dummy docx data", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        res = client.post("/resume/analyze", files=files, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "java" in data["extracted_skills"]
        assert "sql" in data["extracted_skills"]
        assert "matched_jobs" in data


def test_resume_upload_txt():
    token = get_admin_token()
    headers = auth_headers(token)
    
    files = {"file": ("resume.txt", b"Experienced in Git and Fastapi.", "text/plain")}
    res = client.post("/resume/analyze", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "git" in data["extracted_skills"]
    assert "fastapi" in data["extracted_skills"]


def test_leaderboard():
    token = get_admin_token()
    headers = auth_headers(token)
    res = client.get("/leaderboard", headers=headers)
    assert res.status_code == 200


def test_branch_eligibility_and_student_chatbot():
    token = get_admin_token()
    headers = auth_headers(token)

    # 1. Register a student with branch 'IT' and some skills
    res_student = client.post("/auth/register", json={
        "email": "branch_student@test.com", "password": "pass123", "role": "student",
        "name": "Branch Student", "cgpa": 8.5, "branch": "IT", "skills": ["python"]
    })
    assert res_student.status_code == 201
    
    # Login as this student
    login_res = client.post("/auth/login", json={"email": "branch_student@test.com", "password": "pass123"})
    student_token = login_res.json()["access_token"]
    student_headers = auth_headers(student_token)

    # Create two companies: 
    # Company A allows only CSE and ECE
    client.post("/companies", json={
        "name": "CseOnlyCorp", "role": "Dev", "package_lpa": 12.0, "min_cgpa": 7.0,
        "deadline": "2027-01-01T00:00:00", "required_skills": ["python"], "eligible_branches": ["CSE", "ECE"]
    }, headers=headers)
    
    # Company B allows IT
    client.post("/companies", json={
        "name": "ItCorp", "role": "Dev", "package_lpa": 12.0, "min_cgpa": 7.0,
        "deadline": "2027-01-01T00:00:00", "required_skills": ["python"], "eligible_branches": ["IT"]
    }, headers=headers)

    # Test chatbot lagging query for this student
    res_chat = client.post("/chatbot/query", json={"query": "Where am I lagging?"}, headers=student_headers)
    assert res_chat.status_code == 200
    answer = res_chat.json()["answer"]
    assert "Branch Student" in answer
    assert "ItCorp" in answer


def test_resume_upload_twice_overlapping_skills():
    # Register a student with some initial skills
    client.post("/auth/register", json={
        "email": "twice_student@test.com", "password": "pass", "role": "student",
        "name": "Twice Student", "cgpa": 8.0, "branch": "CSE", "skills": ["python", "sql"]
    })
    
    # Login
    login_res = client.post("/auth/login", json={"email": "twice_student@test.com", "password": "pass"})
    token = login_res.json()["access_token"]
    headers = auth_headers(token)
    
    # First resume analysis (updates skills to python, sql, react)
    res1 = client.post("/resume/analyze", json={
        "resume_text": "Skillset includes Python, SQL, and React."
    }, headers=headers)
    assert res1.status_code == 200
    assert "react" in res1.json()["extracted_skills"]

    # Second resume analysis (updates skills with overlapping set: python, sql, docker)
    # This previously failed with IntegrityError due to UNIQUE constraint failed
    res2 = client.post("/resume/analyze", json={
        "resume_text": "Skillset includes Python, SQL, and Docker."
    }, headers=headers)
    assert res2.status_code == 200
    extracted = res2.json()["extracted_skills"]
    assert "docker" in extracted
    assert "react" not in extracted  # react should be cleared as it is not in the new text

