from datetime import datetime

from sqlalchemy import  DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    user: Mapped["User"] = relationship(back_populates="projects")
    boards: Mapped[list["Board"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )