"""
Seeds the database with sample data for local development/demo purposes.
Run with:  python -m app.seed
"""
from datetime import datetime, timedelta

from .database import SessionLocal, engine, Base
from . import models, auth
from .crud_helpers import set_student_skills, set_company_skills


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            print("Database already has data — skipping seed.")
            return

        # --- Admin user ---
        admin_user = models.User(
            email="admin@placement.edu",
            hashed_password=auth.hash_password("admin123"),
            role=models.UserRole.ADMIN,
        )
        db.add(admin_user)

        # --- Students ---
        students_data = [
            dict(name="Ananya Rao", email="ananya@college.edu", phone="9000000001", cgpa=9.1, branch="CSE",
                 resume_link="https://example.com/resume/ananya.pdf", skills=["python", "django", "sql", "git"], past_offers=0),
            dict(name="Rahul Mehta", email="rahul@college.edu", phone="9000000002", cgpa=8.4, branch="IT",
                 resume_link="https://example.com/resume/rahul.pdf", skills=["java", "data structures", "algorithms", "sql"], past_offers=1),
            dict(name="Priya Sharma", email="priya@college.edu", phone="9000000003", cgpa=7.8, branch="CSE",
                 resume_link="https://example.com/resume/priya.pdf", skills=["javascript", "react", "html", "css", "node.js"], past_offers=0),
            dict(name="Karthik Iyer", email="karthik@college.edu", phone="9000000004", cgpa=6.9, branch="ECE",
                 resume_link="https://example.com/resume/karthik.pdf", skills=["c++", "python", "linux"], past_offers=0),
            dict(name="Sneha Gupta", email="sneha@college.edu", phone="9000000005", cgpa=9.4, branch="CSE",
                 resume_link="https://example.com/resume/sneha.pdf", skills=["python", "machine learning", "pandas", "numpy", "tensorflow"], past_offers=2),
            dict(name="Vikram Singh", email="vikram@college.edu", phone="9000000006", cgpa=7.2, branch="ME",
                 resume_link="https://example.com/resume/vikram.pdf", skills=["excel", "leadership"], past_offers=0),
            dict(name="Divya Nair", email="divya@college.edu", phone="9000000007", cgpa=8.9, branch="IT",
                 resume_link="https://example.com/resume/divya.pdf", skills=["aws", "docker", "kubernetes", "linux", "ci/cd"], past_offers=0),
            dict(name="Arjun Verma", email="arjun@college.edu", phone="9000000008", cgpa=6.5, branch="CSE",
                 resume_link="https://example.com/resume/arjun.pdf", skills=["java", "spring", "sql"], past_offers=0),
        ]

        students = []
        for sd in students_data:
            skills = sd.pop("skills")
            offers = sd.pop("past_offers")
            student_user = models.User(
                email=sd["email"], hashed_password=auth.hash_password("student123"), role=models.UserRole.STUDENT
            )
            db.add(student_user)
            db.flush()
            student = models.Student(user_id=student_user.id, past_offers=offers, **sd)
            db.add(student)
            db.flush()
            set_student_skills(db, student, skills)
            students.append(student)

        # --- Companies ---
        now = datetime.utcnow()
        companies_data = [
            dict(name="Infosys", role="Software Engineer", package_lpa=6.5, min_cgpa=6.5,
                 deadline=now + timedelta(days=10), description="Entry-level SDE role.",
                 required_skills=["java", "sql", "data structures"], eligible_branches="CSE, IT, ECE, EE"),
            dict(name="TCS", role="Systems Engineer", package_lpa=4.5, min_cgpa=6.0,
                 deadline=now + timedelta(days=5), description="Systems engineering & support.",
                 required_skills=["python", "sql"], eligible_branches="CSE, IT, ECE, EE, ME, CE"),
            dict(name="Google", role="Software Development Engineer", package_lpa=28.0, min_cgpa=8.5,
                 deadline=now + timedelta(days=20), description="Highly competitive SDE role.",
                 required_skills=["python", "algorithms", "data structures", "c++"], eligible_branches="CSE, IT, ECE, AIDS"),
            dict(name="Amazon", role="Cloud Support Engineer", package_lpa=12.0, min_cgpa=7.5,
                 deadline=now + timedelta(days=2), description="AWS cloud operations role.",
                 required_skills=["aws", "linux", "docker", "kubernetes"], eligible_branches="CSE, IT, ECE"),
            dict(name="Zoho", role="Full Stack Developer", package_lpa=8.0, min_cgpa=7.0,
                 deadline=now + timedelta(days=15), description="Full stack web development.",
                 required_skills=["javascript", "react", "node.js", "sql"], eligible_branches="CSE, IT, ECE, AIDS"),
            dict(name="Fractal Analytics", role="Data Scientist", package_lpa=14.0, min_cgpa=8.0,
                 deadline=now + timedelta(days=8), description="ML & analytics role.",
                 required_skills=["python", "machine learning", "pandas", "numpy"], eligible_branches="CSE, IT, AIDS"),
            dict(name="Microsoft", role="Software Engineer", package_lpa=25.0, min_cgpa=8.0,
                 deadline=now + timedelta(days=12), description="Core Windows & Azure software systems.",
                 required_skills=["c++", "data structures", "algorithms"], eligible_branches="CSE, IT"),
            dict(name="Meta", role="Software Engineer", package_lpa=32.0, min_cgpa=8.5,
                 deadline=now + timedelta(days=18), description="Scale social web & AR systems.",
                 required_skills=["python", "javascript", "react", "algorithms"], eligible_branches="CSE, IT, ECE"),
            dict(name="Netflix", role="Cloud Engineer", package_lpa=35.0, min_cgpa=9.0,
                 deadline=now + timedelta(days=14), description="High throughput media delivery and cloud orchestration.",
                 required_skills=["java", "aws", "docker", "kubernetes"], eligible_branches="CSE, IT"),
            dict(name="Stripe", role="Backend Developer", package_lpa=20.0, min_cgpa=8.0,
                 deadline=now + timedelta(days=25), description="Robust API and financial ledger backend development.",
                 required_skills=["python", "sql", "git"], eligible_branches="CSE, IT, ECE, AIDS"),
            dict(name="Capgemini", role="Software Analyst", package_lpa=4.0, min_cgpa=6.0,
                 deadline=now + timedelta(days=7), description="Consulting and customized application management.",
                 required_skills=["java", "html", "css"], eligible_branches="CSE, IT, ECE, EE, ME"),
            dict(name="Wipro", role="Project Engineer", package_lpa=4.2, min_cgpa=6.0,
                 deadline=now + timedelta(days=4), description="Infrastructure services and app development.",
                 required_skills=["c++", "java", "sql"], eligible_branches="CSE, IT, ECE, EE"),
            dict(name="Cognizant", role="Programmer Analyst", package_lpa=4.5, min_cgpa=6.0,
                 deadline=now + timedelta(days=11), description="Technical support and enterprise systems configuration.",
                 required_skills=["python", "sql", "html"], eligible_branches="CSE, IT, ECE"),
            dict(name="NVIDIA", role="Deep Learning Engineer", package_lpa=26.0, min_cgpa=8.5,
                 deadline=now + timedelta(days=16), description="Building neural networks, cuda optimizations and training systems.",
                 required_skills=["c++", "python", "deep learning", "pytorch"], eligible_branches="CSE, IT, ECE, AIDS"),
            dict(name="Uber", role="Software Engineer", package_lpa=28.0, min_cgpa=8.2,
                 deadline=now + timedelta(days=9), description="Real-time dispatch system development.",
                 required_skills=["java", "algorithms"], eligible_branches="CSE, IT"),
            dict(name="Adobe", role="Member of Technical Staff", package_lpa=22.0, min_cgpa=8.0,
                 deadline=now + timedelta(days=22), description="Developing web creative tools and graphics algorithms.",
                 required_skills=["c++", "java", "data structures", "algorithms"], eligible_branches="CSE, IT, ECE"),
        ]

        companies = []
        for cd in companies_data:
            req_skills = cd.pop("required_skills")
            company = models.Company(**cd)
            db.add(company)
            db.flush()
            set_company_skills(db, company, req_skills)
            companies.append(company)

        db.commit()

        # --- Sample applications & one interview ---
        infosys = companies[0]
        google = companies[2]
        ananya = students[0]
        sneha = students[4]

        app1 = models.Application(student_id=ananya.id, company_id=infosys.id, status=models.ApplicationStatus.SHORTLISTED)
        app2 = models.Application(student_id=sneha.id, company_id=google.id, status=models.ApplicationStatus.SELECTED)
        db.add_all([app1, app2])
        db.flush()

        interview = models.Interview(
            application_id=app1.id, company_id=infosys.id,
            scheduled_at=now + timedelta(days=3), mode=models.InterviewMode.ONLINE,
            meeting_link="https://meet.example.com/infosys-ananya", notes="Technical round 1",
        )
        db.add(interview)
        sneha.past_offers = 3
        db.commit()

        print("Seed complete.")
        print("Admin login -> email: admin@placement.edu | password: admin123")
        print("Student login example -> email: ananya@college.edu | password: student123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
