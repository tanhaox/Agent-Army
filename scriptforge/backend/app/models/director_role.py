import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin


class DirectorRole(Base, BaseMixin):
    __tablename__ = "director_roles"

    script_project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("script_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # anchor / caller / extra
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str | None] = mapped_column(String(20), nullable=True)
    function: Mapped[str | None] = mapped_column(String(200), nullable=True)
    persona_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True,
    )
    storyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    perspective: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    script_project: Mapped["ScriptProject"] = relationship(  # noqa: F821
        backref="director_roles"
    )
