from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.modules.auth.router import router as auth_router
from app.modules.programs.router import router as programs_router
from app.modules.academic_periods.router import router as academic_periods_router
from app.modules.courses.router import router as courses_router
from app.modules.course_groups.router import router as course_groups_router
from app.modules.schedules.router import router as schedules_router
from app.modules.exams.router import router as exams_router
from app.modules.enrollments.router import router as enrollments_router
from app.modules.student_profiles.router import router as student_profiles_router
from app.modules.student.router import router as student_router
from app.modules.documents.router import router as documents_router
from app.modules.faculties.router import router as faculties_router
from app.modules.professors.router import router as professors_router
from app.modules.deadlines.router import router as deadlines_router
from app.modules.notifications.router import router as notifications_router
from app.modules.analytics.router import router as analytics_router
from app.modules.chat.router import router as chat_router
from app.modules.admin.router import router as admin_router
from app.modules.professor.router import router as professor_me_router

app = FastAPI(
    title="UniMate AI API",
    description="Backend API for the Multi-Agent University Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(programs_router)
app.include_router(academic_periods_router)
app.include_router(courses_router)
app.include_router(course_groups_router)
app.include_router(schedules_router)
app.include_router(exams_router)
app.include_router(enrollments_router)
app.include_router(student_profiles_router)
app.include_router(student_router)
app.include_router(documents_router)
app.include_router(faculties_router)
app.include_router(professors_router)
app.include_router(deadlines_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(professor_me_router)


@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "environment": settings.environment,
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/api/health/database")
def database_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "result": result.scalar(),
        }
