"""Fixtures për testet.

Testet punojnë mbi një SQLite in-memory, pa Postgres, pa Qdrant
dhe pa thirrje reale te Claude. Çdo test merr bazë të pastër.
"""

from datetime import time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.exam import Exam
from app.models.program import Program
from app.models.schedule import Schedule
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.core.clock import utcnow


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        first_name="Admin",
        last_name="Test",
        email="admin@test.edu",
        password_hash=hash_password("Admin123!"),
        role=UserRole.ADMIN,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def student_user(db_session) -> User:
    user = User(
        first_name="Arta",
        last_name="Krasniqi",
        email="arta@test.edu",
        password_hash=hash_password("Student123!"),
        role=UserRole.STUDENT,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def academic_data(db_session, student_user):
    """Program, lëndë, orar, provime dhe një student i regjistruar."""

    program = Program(
        name="Shkenca Kompjuterike",
        degree_level="BACHELOR",
        total_ects=180,
        duration_years=3,
    )

    db_session.add(program)
    db_session.flush()

    algorithms = Course(
        code="CS201",
        name="Algoritme dhe Struktura të Dhënash",
        ects=7,
        semester=3,
        program_id=program.id,
    )

    databases = Course(
        code="CS202",
        name="Bazat e të Dhënave",
        ects=6,
        semester=3,
        program_id=program.id,
    )

    unenrolled = Course(
        code="CS301",
        name="Inteligjenca Artificiale",
        ects=7,
        semester=5,
        program_id=program.id,
    )

    db_session.add_all([algorithms, databases, unenrolled])
    db_session.flush()

    profile = StudentProfile(
        user_id=student_user.id,
        student_number="2024-CS-001",
        program_id=program.id,
        study_year=2,
        semester=3,
    )

    db_session.add(profile)
    db_session.flush()

    db_session.add_all(
        [
            Enrollment(
                student_profile_id=profile.id,
                course_id=algorithms.id,
                status="ACTIVE",
            ),
            Enrollment(
                student_profile_id=profile.id,
                course_id=databases.id,
                status="ACTIVE",
            ),
        ]
    )

    db_session.add_all(
        [
            Schedule(
                course_id=algorithms.id,
                day_of_week="Monday",
                start_time=time(9, 0),
                end_time=time(10, 30),
                room="A-201",
            ),
            Schedule(
                course_id=databases.id,
                day_of_week="Thursday",
                start_time=time(14, 0),
                end_time=time(15, 30),
                room="Lab-2",
            ),
        ]
    )

    now = utcnow()

    db_session.add_all(
        [
            Exam(
                course_id=algorithms.id,
                exam_type="FINAL",
                exam_date=now + timedelta(days=21),
                room="A-201",
            ),
            Exam(
                course_id=databases.id,
                exam_type="MIDTERM",
                exam_date=now - timedelta(days=30),
                room="B-104",
            ),
        ]
    )

    db_session.commit()

    return {
        "program": program,
        "profile": profile,
        "algorithms": algorithms,
        "databases": databases,
        "unenrolled": unenrolled,
    }


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
