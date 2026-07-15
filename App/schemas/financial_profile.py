from pydantic import BaseModel, ConfigDict


class FinancialProfileBase(BaseModel):
    user_id: int
    monthly_income: float
    monthly_expenses: float
    existing_debts: float
    financial_health_score: float


class FinancialProfileCreate(FinancialProfileBase):
    pass


class FinancialProfileRead(FinancialProfileBase):
    profile_id: int

    model_config = ConfigDict(from_attributes=True)
