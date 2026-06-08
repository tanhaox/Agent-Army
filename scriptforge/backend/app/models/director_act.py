import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin


class DirectorAct(Base, BaseMixin):
    __tablename__ = "director_acts"

    script_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("script_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    participants: Mapped[dict] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    script_project: Mapped["ScriptProject"] = relationship(  # noqa: F821
        backref="director_acts"
    )
