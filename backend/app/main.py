import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import (
    auth_router, students_router, companies_router, applications_router,
    interviews_router, matching_router, dashboard_router, chatbot_router,
    resume_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Placement Coordinator Agent",
    description="An intelligent system to manage and automate college placement activities.",
    version="1.0.0",
)

# Mount uploads directory to serve uploaded resume files
upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(students_router.router)
app.include_router(companies_router.router)
app.include_router(applications_router.router)
app.include_router(interviews_router.router)
app.include_router(matching_router.router)
app.include_router(dashboard_router.router)
app.include_router(chatbot_router.router)
app.include_router(resume_router.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "Placement Coordinator Agent API"}
