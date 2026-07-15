from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class LoanBase(BaseModel):
    user_id: int
    loan_type: str
    lender_name: str = Field(default="Unknown Lender", description="Name of the lending institution")
    loan_amount: float = Field(gt=0, description="Original loan amount sanctioned")
    outstanding_amount: float = Field(ge=0, description="Current outstanding balance")
    interest_rate: float = Field(ge=0, description="Annual interest rate as a percentage")
    due_date: date = Field(description="Loan due / maturity date (YYYY-MM-DD)")
    overdue_months: int = Field(default=0, ge=0, description="Number of months the loan is overdue")
    emi: float | None = Field(default=None, ge=0, description="Monthly EMI amount (auto-calculated if omitted)")


class LoanCreate(LoanBase):
    """Payload to create a new loan record."""
    pass


class LoanUpdate(BaseModel):
    """Partial update — all fields are optional."""
    loan_type: str | None = None
    lender_name: str | None = None
    loan_amount: float | None = Field(default=None, gt=0)
    outstanding_amount: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0)
    due_date: date | None = None
    overdue_months: int | None = Field(default=None, ge=0)
    emi: float | None = Field(default=None, ge=0)


class LoanRead(LoanBase):
    loan_id: int

    model_config = ConfigDict(from_attributes=True)


class LoanPriority(BaseModel):
    """Priority + settlement details for a single loan."""
    loan_id: int
    loan_type: str
    lender_name: str
    outstanding_amount: float
    interest_rate: float
    overdue_months: int
    settlement_percentage: float
    recommended_settlement_amount: float
    priority: str
    priority_score: int
    settlement_prediction: str
