from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CourseGroup(Base):
    """Një grup (paralele) i një lënde, me profesorin e vet.

    E njëjta lëndë mund të ligjërohet nga disa profesorë, secili te
    grupi i vet. Studenti regjistrohet në një grup, dhe kështu dihet
    cili profesor i jep mësim; `Course.professor_id` mbetet
    koordinatori i lëndës.
    """

    __tablename__ = "course_groups"
    __table_args__ = (
        UniqueConstraint("course_id", "name", name="uq_course_groups_course_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    professor_id: Mapped[int | None] = mapped_column(
        ForeignKey("professors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Sa studentë pranon grupi; bosh = pa kufi.
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    course = relationship("Course", back_populates="groups")
    professor = relationship("Professor")
