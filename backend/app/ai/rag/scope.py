"""Cilat dokumente mund t'i përdorë asistenti për një përdorues.

Çdo dokument i përket gjithë universitetit, një fakulteti ose një
lënde. Pa këtë kufizim, një student që pyet për "rregulloren e
provimeve" mund të merrte rregulloren e një fakulteti tjetër, me
rregulla të ndryshme — përgjigje e cituar saktë, por e gabuar për të.

- Studenti: universiteti + fakulteti i programit të tij + lëndët e
  programit të tij (edhe ato ku s'është regjistruar ende, si katalog).
  Materialet e një grupi (ligjëratat e një profesori) vetëm kur është
  në atë grup: studenti i Grupit A mëson nga ligjëratat e profesorit
  të vet, jo nga ato të kolegut që jep të njëjtën lëndë.
- Profesori: universiteti + fakulteti i tij + lëndët që ligjëron, me
  materialet e të gjitha grupeve të tyre.
- Administratori: gjithçka (`None` = pa filtër).
"""

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.teaching import teaches_course
from app.models.course import Course
from app.models.document import Document
from app.models.enrollment import Enrollment
from app.models.professor import Professor
from app.models.program import Program
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole


def accessible_document_ids(user: User, db: Session) -> list[int] | None:
    if user.role == UserRole.ADMIN:
        return None

    faculty_id: int | None = None
    course_ids: list[int] = []

    # None: pa kufizim sipas grupit (profesori). Listë: grupet e studentit.
    group_ids: list[int] | None = None

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
            group_ids = [
                group_id
                for group_id in db.scalars(
                    select(Enrollment.group_id).where(
                        Enrollment.student_profile_id == profile.id,
                        Enrollment.status == "ACTIVE",
                        Enrollment.group_id.is_not(None),
                    )
                )
            ]

    elif user.role == UserRole.PROFESSOR:
        professor = db.scalar(
            select(Professor).where(Professor.user_id == user.id)
        )

        if professor is not None:
            faculty_id = professor.faculty_id
            course_ids = list(
                db.scalars(
                    select(Course.id).where(teaches_course(professor.id))
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
        course_condition = Document.course_id.in_(course_ids)

        if group_ids is not None:
            course_condition = and_(
                course_condition,
                or_(
                    Document.group_id.is_(None),
                    Document.group_id.in_(group_ids),
                ),
            )

        conditions.append(course_condition)

    return list(
        db.scalars(
            select(Document.id).where(
                Document.is_active.is_(True),
                or_(*conditions),
            )
        )
    )
