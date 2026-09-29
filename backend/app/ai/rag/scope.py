"""Cilat dokumente mund t'i përdorë asistenti për një përdorues.

Çdo dokument i përket gjithë universitetit, një fakulteti ose një
lënde. Pa këtë kufizim, një student që pyet për "rregulloren e
provimeve" mund të merrte rregulloren e një fakulteti tjetër, me
rregulla të ndryshme — përgjigje e cituar saktë, por e gabuar për të.

- Studenti: universiteti + fakulteti i programit të tij + lëndët e
  programit të tij (edhe ato ku s'është regjistruar ende, si katalog).
- Profesori: universiteti + fakulteti i tij + lëndët që ligjëron.
- Administratori: gjithçka (`None` = pa filtër).
"""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.document import Document
from app.models.professor import Professor
from app.models.program import Program
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole


def accessible_document_ids(user: User, db: Session) -> list[int] | None:
    if user.role == UserRole.ADMIN:
        return None

    faculty_id: int | None = None
    course_ids: list[int] = []

    if user.role == UserRole.STUDENT:
        profile = db.scalar(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )

        if profile is not None:
            program = db.get(Program, profile.program_id)
            faculty_id = program.faculty_id if program else None
            course_ids = list(
                db.scalars(
                    select(Course.id).where(
                        Course.program_id == profile.program_id
                    )
                )
            )

    elif user.role == UserRole.PROFESSOR:
        professor = db.scalar(
            select(Professor).where(Professor.user_id == user.id)
        )

        if professor is not None:
            faculty_id = professor.faculty_id
            course_ids = list(
                db.scalars(
                    select(Course.id).where(
                        Course.professor_id == professor.id
                    )
                )
            )

    conditions = [
        # Dokumentet e gjithë universitetit.
        and_(Document.faculty_id.is_(None), Document.course_id.is_(None)),
    ]

    # Dokumentet e fakultetit që nuk i përkasin një lënde të caktuar;
    # ato të lëndëve kalojnë vetëm përmes `course_ids`.
    if faculty_id is not None:
        conditions.append(
            and_(
                Document.faculty_id == faculty_id,
                Document.course_id.is_(None),
            )
        )

    if course_ids:
        conditions.append(Document.course_id.in_(course_ids))

    return list(
        db.scalars(
            select(Document.id).where(
                Document.is_active.is_(True),
                or_(*conditions),
            )
        )
    )
