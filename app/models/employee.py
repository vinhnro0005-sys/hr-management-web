from datetime import date
from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(100))
    birthday: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    address: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[date | None] = mapped_column(Date)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    status: Mapped[str] = mapped_column(String(20), default="Active", server_default="Active")