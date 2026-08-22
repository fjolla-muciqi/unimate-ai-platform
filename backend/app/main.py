from fastapi import FastAPI
from sqlalchemy import text
from app.core.database import engine 
from app.modules.auth.router import router as auth_router
from app.modules.programs.router import router as programs_router
from app.modules.courses.router import router as courses_router
from app.modules.schedules.router import router as schedules_router
from app.modules.exams.router import router as exams_router
from app.modules.enrollments.router import router as enrollments_router
from app.modules.student_profiles.router import router as student_profiles_router
from app.modules.student.router import router as student_router
from app.modules.documents.router import router as documents_router

app = FastAPI(
    title="UniMate AI API",
    description="Backend API for the Multi-Agent University Assistant",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(programs_router)
app.include_router(courses_router)
app.include_router(schedules_router)
app.include_router(exams_router)
app.include_router(enrollments_router)
app.include_router(student_profiles_router)
app.include_router(student_router)
app.include_router(documents_router)

@app.get("/")
def root():
    return {
        "application": "UniMate AI",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.get("/api/health/database")
def database_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "result": result.scalar()
        }