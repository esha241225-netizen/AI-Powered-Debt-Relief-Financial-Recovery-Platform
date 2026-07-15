from pydantic import BaseModel, ConfigDict

from app.schemas.ai_history import AIHistoryRead
from app.schemas.financial_profile import FinancialProfileRead
from app.schemas.loan import LoanRead
from app.schemas.settlement_record import SettlementRecordRead
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    message: str
    user: UserRead
    access_token: str | None = None
    token_type: str | None = None
    expires_in_minutes: int | None = None


class MeResponse(BaseModel):
    user: UserRead
    financial_profile: FinancialProfileRead | None = None


class UpdateProfileRequest(BaseModel):
    user_id: int
    name: str | None = None
    email: str | None = None
    password: str | None = None
    monthly_income: float | None = None
    monthly_expenses: float | None = None
    existing_debts: float | None = None
    financial_health_score: float | None = None


class UpdateProfileResponse(BaseModel):
    message: str
    user: UserRead
    financial_profile: FinancialProfileRead | None = None


class FinancialHealthResponse(BaseModel):
    user_id: int
    score: float
    status: str
    message: str


class SettlementPredictionRequest(BaseModel):
    user_id: int


class SettlementPredictionItem(BaseModel):
    loan_id: int
    loan_type: str = ""
    lender_name: str
    loan_amount: float = 0.0
    outstanding_amount: float
    interest_rate: float
    overdue_months: int
    emi: float
    # Settlement engine outputs
    settlement_percentage: float = 0.0
    suggested_settlement_percentage: float = 0.0  # alias for backward compat
    recommended_settlement_amount: float
    settlement_prediction: str = ""
    # Priority engine outputs
    priority: str = ""
    priority_score: int = 0
    risk_score: int = 0
    risk_category: str = ""
    # Generated letter
    negotiation_letter: str = ""


class SettlementPredictionResponse(BaseModel):
    user_id: int
    total_emi: float
    total_outstanding: float
    surplus: float
    emi_ratio_percent: float
    debt_to_income_percent: float
    settlement_results: list[SettlementPredictionItem]


# ---------------------------------------------------------------------------
# Loan portfolio summary
# ---------------------------------------------------------------------------


class LoanPortfolioSummary(BaseModel):
    """High-level aggregates for a user's entire loan portfolio."""
    user_id: int
    total_loans: int
    total_loan_amount: float
    total_outstanding: float
    total_emi: float
    overdue_loans: int
    high_priority_loans: int
    medium_priority_loans: int
    low_priority_loans: int
    emi_ratio_percent: float
    debt_to_income_percent: float
    stress_level: str


# ---------------------------------------------------------------------------
# Manual settlement record creation
# ---------------------------------------------------------------------------


class ManualSettlementRequest(BaseModel):
    """Create a settlement record manually (without running the full predictor)."""
    user_id: int
    loan_id: int
    settlement_percentage: float
    recommended_amount: float
    priority_level: str
    negotiation_letter: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Negotiation letter standalone response
# ---------------------------------------------------------------------------


class NegotiationLetterResponse(BaseModel):
    settlement_id: int
    loan_id: int
    loan_type: str
    lender_name: str
    settlement_percentage: float
    recommended_amount: float
    priority_level: str
    negotiation_letter: str
    created_at: str


class NegotiationStrategyRequest(BaseModel):
    user_id: int
    loan_id: int


class NegotiationStrategyResponse(BaseModel):
    history_id: int
    user_id: int
    loan_id: int
    negotiation_strategy: str


class NegotiationEmailResponse(BaseModel):
    history_id: int
    user_id: int
    loan_id: int
    subject: str
    body: str


class TimelinePoint(BaseModel):
    month: int
    projected_remaining: float


class DebtTimelinePoint(BaseModel):
    month: int
    remaining_balance: float


class DebtTimelineResponse(BaseModel):
    user_id: int
    total_outstanding: float
    months_to_debt_free: int
    final_remaining_balance: float
    timeline_preview: list[DebtTimelinePoint]


class DashboardSummary(BaseModel):
    total_loans: int
    total_outstanding: float
    settlement_records: int
    ai_history: int
    financial_health_score: float
    financial_health_status: str


class DashboardDataResponse(BaseModel):
    user: UserRead
    financial_profile: FinancialProfileRead | None
    loans: list[LoanRead]
    loan_priorities: list[dict[str, object]]
    settlement_records: list[SettlementRecordRead]
    ai_history: list[AIHistoryRead]
    summary: DashboardSummary


# ---------------------------------------------------------------------------
# Inline input schemas for AI endpoints
# (frontend can POST loan + profile data directly — no pre-existing DB record needed)
# ---------------------------------------------------------------------------


class LoanInput(BaseModel):
    """A single loan's details as submitted by the frontend."""

    loan_id: int | None = None
    loan_type: str
    lender_name: str = "Unknown Lender"
    loan_amount: float
    outstanding_amount: float
    interest_rate: float
    due_date: str  # ISO 8601 date string, e.g. "2025-12-31"
    overdue_months: int = 0
    emi: float | None = None


class FinancialProfileInput(BaseModel):
    """Financial profile details as submitted by the frontend."""

    monthly_income: float
    monthly_expenses: float
    existing_debts: float = 0.0
    financial_health_score: float = 0.0


# ---------------------------------------------------------------------------
# AI Negotiation Strategy (direct-request)
# ---------------------------------------------------------------------------


class AIStrategyRequest(BaseModel):
    """Request body for POST /ai/negotiation-strategy."""

    user_id: int
    financial_profile: FinancialProfileInput
    loans: list[LoanInput]


class AIStrategyResponse(BaseModel):
    """Structured response for the negotiation strategy endpoint."""

    user_id: int
    strategy: str
    financial_health: dict
    ai_enhanced: bool
    history_id: int | None = None


# ---------------------------------------------------------------------------
# AI Settlement Analysis (direct-request)
# ---------------------------------------------------------------------------


class AISettlementAnalysisRequest(BaseModel):
    """Request body for POST /ai/settlement-analysis."""

    user_id: int
    financial_profile: FinancialProfileInput
    loans: list[LoanInput]


class LoanSpecificAdviceItem(BaseModel):
    loan_type: str
    advice: str
    urgency: str


class AISettlementAnalysisResponse(BaseModel):
    """Structured response for the settlement analysis endpoint."""

    user_id: int
    financial_health: dict
    settlement_results: list[dict]
    ai_analysis: dict
    history_id: int | None = None


# ---------------------------------------------------------------------------
# AI Loan Advice (direct-request)
# ---------------------------------------------------------------------------


class AILoanAdviceRequest(BaseModel):
    """Request body for POST /ai/loan-advice."""

    user_id: int
    financial_profile: FinancialProfileInput
    loans: list[LoanInput]


class AILoanAdviceResponse(BaseModel):
    """Structured response for the loan advice endpoint."""

    user_id: int
    financial_health: dict
    advice: dict
    history_id: int | None = None


# ---------------------------------------------------------------------------
# AI Repayment Plan (direct-request)
# ---------------------------------------------------------------------------


class AIRepaymentPlanRequest(BaseModel):
    """Request body for POST /ai/repayment-plan."""

    user_id: int
    financial_profile: FinancialProfileInput
    loans: list[LoanInput]
    extra_monthly_payment: float = 0.0


class AIRepaymentPlanResponse(BaseModel):
    """Structured response for the repayment plan endpoint."""

    user_id: int
    financial_health: dict
    repayment_plan: dict
    history_id: int | None = None


# ---------------------------------------------------------------------------
# AI Negotiation Email (direct-request)
# ---------------------------------------------------------------------------


class AIEmailRequest(BaseModel):
    """Request body for POST /ai/negotiation-email."""

    user_id: int
    loan: LoanInput
    financial_profile: FinancialProfileInput


class AIEmailResponse(BaseModel):
    """Structured response for the negotiation email endpoint."""

    user_id: int
    loan_type: str
    lender_name: str
    outstanding_amount: float
    recommended_settlement_amount: float
    subject: str
    body: str
    ai_enhanced: bool
    history_id: int | None = None
