from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Board(Base):
    __tablename__ = "boards"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(default=0)
    color: Mapped[str] = mapped_column(String(20), nullable=False, server_default="gray")
    
    project: Mapped["Project"] = relationship(back_populates="boards")
    cards: Mapped[list["Card"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
    )