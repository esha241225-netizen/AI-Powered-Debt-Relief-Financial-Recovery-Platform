from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SettlementRecord(Base):
    __tablename__ = "settlement_records"

    settlement_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.loan_id"), nullable=False, index=True)

    # --- Denormalised for fast reporting (no joins needed) ---
    loan_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    lender_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    # --- Settlement outcome ---
    settlement_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    settlement_prediction: Mapped[str] = mapped_column(String(255), nullable=False)
    recommended_amount: Mapped[float] = mapped_column(Float, nullable=False)
    priority_level: Mapped[str] = mapped_column(String(50), nullable=False)

    # --- Generated negotiation letter (stored in full) ---
    negotiation_letter: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="settlement_records")
    loan = relationship("Loan", back_populates="settlement_records")
