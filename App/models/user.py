from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Indexed for fast login lookups per session
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Stored as bcrypt hash from registration onwards
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    loans = relationship("Loan", back_populates="user", cascade="all, delete-orphan")
    financial_profile = relationship(
        "FinancialProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    settlement_records = relationship("SettlementRecord", back_populates="user", cascade="all, delete-orphan")
    ai_history = relationship("AIHistory", back_populates="user", cascade="all, delete-orphan")
