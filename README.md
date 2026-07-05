# Placement Coordinator Agent

An intelligent, full-stack system for managing and automating college placement
activities: student & company records, application workflows, interview
scheduling, notifications, analytics, and rule-based AI features (eligibility
matching, recommendations, a chatbot, resume analysis, skill-gap analysis,
and a leaderboard).

---

## 1. High-Level Architecture

```
┌─────────────────────┐        JWT-authenticated REST API        ┌──────────────────────┐
│   React Frontend     │  ───────────────────────────────────▶  │   FastAPI Backend     │
│  (Vite + Tailwind)   │  ◀───────────────────────────────────  │  (SQLAlchemy ORM)     │
└─────────────────────┘                                          └──────────┬───────────┘
                                                                             │
                                                                             ▼
                                                                  ┌──────────────────────┐
                                                                  │  SQLite (dev) /       │
                                                                  │  PostgreSQL (prod)    │
                                                                  └──────────────────────┘
```

- **Backend**: FastAPI + SQLAlchemy. Stateless JWT auth, role-based access
  control (Admin / Student). All "AI" features (eligibility engine,
  recommendations, chatbot, resume analyzer) are transparent, rule-based
  logic in `app/scoring.py` — no external paid AI APIs, fully explainable.
- **Frontend**: React (Vite) + Tailwind CSS, React Router, Axios, Recharts
  for analytics charts, lucide-react for icons.
- **Database**: SQLite by default (zero setup for local dev); switches to
  PostgreSQL by simply setting the `DATABASE_URL` environment variable —
  no code changes needed.

### Folder structure

```
placement-coordinator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + router registration
│   │   ├── database.py          # SQLAlchemy engine/session (SQLite/Postgres)
│   │   ├── models.py            # All ORM tables & relationships
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── auth.py              # JWT creation/validation, password hashing, RBAC
│   │   ├── scoring.py           # Eligibility/recommendation/skill-gap/resume logic
│   │   ├── notifications.py     # Mock notification/alert system
│   │   ├── crud_helpers.py      # Shared skill-linking & serialization helpers
│   │   ├── seed.py              # Sample data seeder
│   │   └── routers/
│   │       ├── auth_router.py
│   │       ├── students_router.py
│   │       ├── companies_router.py
│   │       ├── applications_router.py
│   │       ├── interviews_router.py     # also serves /notifications
│   │       ├── matching_router.py       # eligibility, recommendations, skill-gap, leaderboard
│   │       ├── dashboard_router.py
│   │       ├── chatbot_router.py
│   │       └── resume_router.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── main.jsx / App.jsx
    │   ├── api.js                 # Axios client with JWT interceptor
    │   ├── context/AuthContext.jsx
    │   ├── components/            # Layout, shared UI pieces
    │   └── pages/                 # Login, Register, Admin*, Student*, Chatbot, Leaderboard
    ├── package.json
    └── vite.config.js
```

---

## 2. Database Schema

| Table            | Purpose                                                                 |
|-------------------|--------------------------------------------------------------------------|
| `users`           | Login credentials + `role` (admin/student), PK `id`                     |
| `students`        | Student profile; FK `user_id` → `users.id` (nullable, 1:1)              |
| `skills`          | Normalized skill names (unique)                                          |
| `student_skills`  | M:N join, FK `student_id`, `skill_id`                                    |
| `companies`       | Company + job posting; min CGPA, package, deadline                      |
| `company_skills`  | M:N join, FK `company_id`, `skill_id`                                    |
| `applications`    | FK `student_id`, `company_id`; unique constraint prevents duplicates    |
| `interviews`      | FK `application_id` (1:1), `company_id`; date, mode, meeting link        |

Indexes: `students.cgpa`, `applications.status`, plus standard PK/FK indexes.
Duplicate applications are prevented by a DB-level unique constraint on
`(student_id, company_id)`, in addition to an application-layer check.

---

## 3. Core Feature → Endpoint Map

| Feature                     | Endpoint(s)                                                       |
|------------------------------|---------------------------------------------------------------------|
| Auth (JWT, RBAC)             | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`          |
| Student management           | `GET/POST /students`, `GET/PUT/DELETE /students/{id}`              |
| Company management            | `GET/POST /companies`, `GET/PUT/DELETE /companies/{id}`            |
| Application tracking          | `GET/POST /applications`, `PATCH /applications/{id}/status`, `DELETE /applications/{id}` |
| Eligibility engine             | `GET /eligibility/{company_id}`                                    |
| Recommendations                | `GET /recommendations/students-for-job/{company_id}`, `GET /recommendations/jobs-for-student/{student_id}` |
| Skill gap analyzer              | `GET /skill-gap/{student_id}/{company_id}`                          |
| Leaderboard                     | `GET /leaderboard`                                                  |
| Interview scheduling             | `GET/POST /interviews`, `DELETE /interviews/{id}`                   |
| Notifications                    | `GET /notifications`                                                |
| Analytics dashboard              | `GET /dashboard`                                                    |
| AI Chatbot                       | `POST /chatbot/query`                                               |
| Resume analyzer                  | `POST /resume/analyze`                                              |

Interactive API docs (Swagger UI) are auto-generated at **`/docs`** once the
backend is running, with a "Try it out" button for every endpoint.

### Sample request/response

**Login**
```
POST /auth/login
{ "email": "admin@placement.edu", "password": "admin123" }

→ 200 OK
{ "access_token": "eyJ...", "token_type": "bearer", "role": "admin", "user_id": 1, "student_id": null }
```

**Eligibility engine**
```
GET /eligibility/1
Authorization: Bearer <token>

→ 200 OK
[
  { "student_id": 2, "name": "Rahul Mehta", "cgpa": 8.4,
    "matched_skills": ["data structures", "java", "sql"],
    "skill_match_pct": 100.0, "score": 86.0 },
  ...
]
```

**Chatbot**
```
POST /chatbot/query
{ "query": "Show top 5 candidates for TCS" }

→ 200 OK
{ "answer": "Here are the top 5 candidates for TCS (Systems Engineer).", "data": [...] }
```

---

## 4. Scoring Logic (the "AI")

All matching is transparent and rule-based (`app/scoring.py`):

```
score = (skill_match_pct * 0.6) + (cgpa_normalized * 0.25) + (past_performance_normalized * 0.15)
```

- **Eligibility** = CGPA ≥ company's minimum AND at least one required skill matches.
- **Skill match %** = (matched required skills) / (total required skills) × 100.
- **Resume analyzer** does keyword extraction with word-boundary matching
  against a curated skill list, then maps found skills to likely roles.
- **Leaderboard** ranks by a composite of normalized CGPA, distinct skill
  count, and past placement count.

---

## 5. Setup Guide

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Seed sample data (creates placement.db with demo students/companies)
python -m app.seed

# Run the API (http://localhost:8000, docs at /docs)
uvicorn app.main:app --reload
```

To use PostgreSQL instead of SQLite:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/placement_db"
```

Default demo logins after seeding:
- Admin: `admin@placement.edu` / `admin123`
- Student: `ananya@college.edu` / `student123` (and 7 other seeded students, password `student123`)

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The frontend reads the API URL from `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

### Running tests

```bash
cd backend
pytest
```

---

## 6. Future Improvements

- Real email/SMS delivery (SendGrid/Twilio) instead of the mock console notifier
- WebSocket-based live notifications instead of polling `/notifications`
- File upload for resumes (PDF parsing) instead of pasted resume text
- Pagination & full-text search indexes for large student/company datasets
- Replace the rule-based recommender with a learned model once enough
  historical placement outcome data exists
- Audit log / activity history per application
- Dockerfile + docker-compose for one-command deployment
