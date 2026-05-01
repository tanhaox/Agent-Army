from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseMixin

import uuid


class User(Base, BaseMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan_type: Mapped[str] = mapped_column(String(20), default="free")
    quota_total: Mapped[int] = mapped_column(Integer, default=5)
    quota_used: Mapped[int] = mapped_column(Integer, default=0)
    settings: Mapped[dict | None] = mapped_column(JSON, default=dict)

    room_tones: Mapped[list["RoomTone"]] = relationship(back_populates="creator")  # noqa: F821
    personas: Mapped[list["Persona"]] = relationship(back_populates="creator")  # noqa: F821
    guest_identities: Mapped[list["GuestIdentity"]] = relationship(back_populates="creator")  # noqa: F821
    script_projects: Mapped[list["ScriptProject"]] = relationship(back_populates="creator")  # noqa: F821
    learning_materials: Mapped[list["LearningMaterial"]] = relationship(back_populates="uploader")  # noqa: F821
