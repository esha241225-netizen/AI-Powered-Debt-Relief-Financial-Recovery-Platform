from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Loan(Base):
    __tablename__ = "loans"

    loan_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)

    # --- Core loan details ---
    loan_type: Mapped[str] = mapped_column(String(100), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(200), nullable=False, default="Unknown Lender")
    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    outstanding_amount: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Repayment tracking (drives settlement % and priority) ---
    overdue_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    emi: Mapped[float | None] = mapped_column(Float, nullable=True)

    user = relationship("User", back_populates="loans")
    settlement_records = relationship(
        "SettlementRecord", back_populates="loan", cascade="all, delete-orphan"
    )
