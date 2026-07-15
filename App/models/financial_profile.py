from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), unique=True, nullable=False, index=True)
    monthly_income: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_expenses: Mapped[float] = mapped_column(Float, nullable=False)
    existing_debts: Mapped[float] = mapped_column(Float, nullable=False)
    financial_health_score: Mapped[float] = mapped_column(Float, nullable=False)

    user = relationship("User", back_populates="financial_profile")
