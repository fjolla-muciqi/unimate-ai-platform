"""Kush jep mësim ku: i vetmi vend që e vendos këtë.

Një lëndë ka një koordinator (`Course.professor_id`) dhe një ose më
shumë grupe, secili me profesorin e vet. Studenti regjistrohet në një
grup. Nga kjo rrjedhin rregullat e mëposhtme, që i përdorin njësoj
faqet e profesorit, agjentët, dokumentet dhe kërkimi:

- Profesori ligjëron një lëndë kur është koordinatori i saj ose
  profesori i të paktën një grupi.
- Profesori sheh studentët e grupeve të veta, dhe ata pa grup vetëm
  te lëndët që koordinon — jo studentët e grupit të një kolegu që jep
  të njëjtën lëndë.
- Orari pa grup është i përbashkët për gjithë lëndën; orari me grup
  vlen vetëm për studentët dhe profesorin e atij grupi.

Funksionet kthejnë kushte SQLAlchemy, që filtri të jetë gjithmonë
brenda query-t dhe jo pas tij.
"""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_group import CourseGroup
from app.models.enrollment import Enrollment
from app.models.professor import Professor
from app.models.schedule import Schedule


def professor_group_ids(professor_id: int):
    return select(CourseGroup.id).where(
        CourseGroup.professor_id == professor_id
    )


def teaches_course(professor_id: int):
    """Kushti mbi `Course`: profesori e koordinon ose jep një grup të saj."""

    return or_(
        Course.professor_id == professor_id,
        Course.id.in_(
            select(CourseGroup.course_id).where(
                CourseGroup.professor_id == professor_id
            )
        ),
    )


def professor_sees_enrollment(professor_id: int):
    """Kushti mbi `Enrollment` (me `Course` të bashkuar në query)."""

    return or_(
        Enrollment.group_id.in_(professor_group_ids(professor_id)),
        and_(
            Enrollment.group_id.is_(None),
            Course.professor_id == professor_id,
        ),
    )


def professor_sees_schedule(professor_id: int):
    """Kushti mbi `Schedule` (me `Course` të bashkuar në query)."""

    return and_(
        teaches_course(professor_id),
        or_(
            Schedule.group_id.is_(None),
            Schedule.group_id.in_(professor_group_ids(professor_id)),
        ),
    )


def student_sees_schedule():
    """Kushti mbi `Schedule` (me `Enrollment` të studentit të bashkuar)."""

    return or_(
        Schedule.group_id.is_(None),
        Schedule.group_id == Enrollment.group_id,
    )


def count_professor_students(
    professor_id: int, course_id: int, db: Session
) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Enrollment)
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            Enrollment.course_id == course_id,
            Enrollment.status == "ACTIVE",
            professor_sees_enrollment(professor_id),
        )
    ) or 0


def least_filled_group(course_id: int, db: Session) -> CourseGroup | None:
    """Grupi me më pak studentë që ka ende vend, për regjistrimin automatik."""

    groups = db.scalars(
        select(CourseGroup)
        .where(CourseGroup.course_id == course_id)
        .order_by(CourseGroup.name)
    ).all()

    best: CourseGroup | None = None
    best_count = 0

    for group in groups:
        count = db.scalar(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.group_id == group.id,
                Enrollment.status == "ACTIVE",
            )
        ) or 0

        if group.capacity is not None and count >= group.capacity:
            continue

        if best is None or count < best_count:
            best, best_count = group, count

    return best


def teacher_of_enrollment(
    enrollment: Enrollment, course: Course, db: Session
) -> Professor | None:
    """Profesori i grupit të studentit; pa grup, koordinatori i lëndës."""

    if enrollment.group_id is not None:
        group = db.get(CourseGroup, enrollment.group_id)

        if group is not None and group.professor_id is not None:
            return db.get(Professor, group.professor_id)

    if course.professor_id is not None:
        return db.get(Professor, course.professor_id)

    return None


def group_belongs_to_course(
    group_id: int | None, course_id: int, db: Session
) -> bool:
    """Një grup bosh vlen gjithmonë; përndryshe duhet të jetë i lëndës."""

    if group_id is None:
        return True

    group = db.get(CourseGroup, group_id)

    return group is not None and group.course_id == course_id
