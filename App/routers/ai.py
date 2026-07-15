"""
routers/ai.py
=============
AI-powered API endpoints for FinRelief AI.

All endpoints accept frontend requests containing loan details and a
financial profile in the request body, validate input via Pydantic schemas,
delegate AI generation to ``app.core.ai_engine``, and return structured
JSON responses.

Endpoints
---------
POST /ai/negotiation-strategy   — full negotiation strategy via Gemini
POST /ai/settlement-analysis    — AI-enhanced settlement analysis per loan
POST /ai/loan-advice            — personalised per-loan action plan
POST /ai/repayment-plan         — avalanche repayment plan with timeline
POST /ai/negotiation-email      — professional lender letter generation
GET  /ai/health                 — AI engine health check
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.ai_engine import (
    generate_loan_advice,
    generate_negotiation_email,
    generate_negotiation_strategy,
    generate_repayment_plan,
    generate_settlement_analysis,
)
from app.core.auth import CurrentUser
from app.core.logic import (
    calculate_financial_health,
    calculate_settlement_recommendations,
)
from app.db.session import get_db
from app.models.ai_history import AIHistory
from app.models.user import User
from app.schemas.api import (
    AIEmailRequest,
    AIEmailResponse,
    AILoanAdviceRequest,
    AILoanAdviceResponse,
    AIRepaymentPlanRequest,
    AIRepaymentPlanResponse,
    AISettlementAnalysisRequest,
    AISettlementAnalysisResponse,
    AIStrategyRequest,
    AIStrategyResponse,
)

router = APIRouter(prefix="/ai", tags=["AI Engine"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _loan_dicts(loans_input) -> list[dict]:
    """Convert a list of LoanInput Pydantic models to plain dicts."""
    return [loan.model_dump() for loan in loans_input]


def _profile_dict(profile_input) -> dict:
    """Convert a FinancialProfileInput Pydantic model to a plain dict."""
    return profile_input.model_dump()


def _resolve_user(user_id: int, db: Session) -> User:
    """Fetch user from DB or raise 404."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )
    return user


def _save_ai_history(
    db: Session,
    user_id: int,
    negotiation_strategy: str,
    settlement_letter: str,
    ai_response: str,
) -> AIHistory:
    """Persist an AI interaction to the ai_history table."""
    record = AIHistory(
        user_id=user_id,
        negotiation_strategy=negotiation_strategy,
        settlement_letter=settlement_letter,
        ai_response=ai_response,
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        return record
    return record


# ---------------------------------------------------------------------------
# POST /ai/negotiation-strategy
# ---------------------------------------------------------------------------


@router.post(
    "/negotiation-strategy",
    response_model=AIStrategyResponse,
    summary="Generate AI-powered negotiation strategy",
    description=(
        "Accepts the user's loan details and financial profile, computes financial "
        "health metrics, calls Google Gemini to produce a personalised negotiation "
        "strategy, and returns structured JSON. Falls back to rule-based logic when "
        "Gemini is unavailable."
    ),
)
def ai_negotiation_strategy(
    payload: AIStrategyRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AIStrategyResponse:
    """Generate a personalised debt-negotiation strategy."""
    user = _resolve_user(payload.user_id, db)

    loan_list = _loan_dicts(payload.loans)
    profile = _profile_dict(payload.financial_profile)

    # Validate at least one loan is provided
    if not loan_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one loan must be provided to generate a strategy.",
        )

    # Compute financial health using core logic (works with dicts via duck typing)
    financial_health = calculate_financial_health(payload.financial_profile, payload.loans)

    # Call AI engine
    strategy_text = generate_negotiation_strategy(
        user_name=user.name,
        financial_profile=profile,
        loans=loan_list,
        financial_health=financial_health,
        settlement_data={},
    )

    ai_enhanced = "[ai_engine]" not in strategy_text and len(strategy_text) > 200

    # Persist to history
    history = _save_ai_history(
        db=db,
        user_id=payload.user_id,
        negotiation_strategy=strategy_text,
        settlement_letter="",
        ai_response=(
            f"Strategy generated. Stress level: {financial_health.get('stress_level', 'N/A')}. "
            f"AI model used: {'Gemini' if ai_enhanced else 'Rule-based fallback'}."
        ),
    )

    return AIStrategyResponse(
        user_id=payload.user_id,
        strategy=strategy_text,
        financial_health=financial_health,
        ai_enhanced=ai_enhanced,
        history_id=history.history_id,
    )


# ---------------------------------------------------------------------------
# POST /ai/settlement-analysis
# ---------------------------------------------------------------------------


@router.post(
    "/settlement-analysis",
    response_model=AISettlementAnalysisResponse,
    summary="AI-enhanced settlement analysis for all loans",
    description=(
        "Computes per-loan settlement recommendations, then calls Gemini to produce "
        "an executive summary, priority actions, and risk assessment. Returns a "
        "fully structured JSON response."
    ),
)
def ai_settlement_analysis(
    payload: AISettlementAnalysisRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AISettlementAnalysisResponse:
    """Return AI-enhanced settlement analysis per loan."""
    user = _resolve_user(payload.user_id, db)

    loan_list = _loan_dicts(payload.loans)
    profile = _profile_dict(payload.financial_profile)

    if not loan_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one loan is required for settlement analysis.",
        )

    # Rule-based settlement calculations
    financial_health = calculate_financial_health(payload.financial_profile, payload.loans)
    settlement_data = calculate_settlement_recommendations(
        payload.financial_profile, payload.loans, None
    )
    settlement_results = settlement_data.get("settlement_results", [])

    # AI enhancement
    ai_analysis = generate_settlement_analysis(
        user_name=user.name,
        financial_profile=profile,
        loans=loan_list,
        settlement_results=settlement_results,
    )

    # Persist
    summary_text = ai_analysis.get("summary", "")
    history = _save_ai_history(
        db=db,
        user_id=payload.user_id,
        negotiation_strategy=summary_text,
        settlement_letter="",
        ai_response=(
            f"Settlement analysis: {len(settlement_results)} loan(s) analysed. "
            f"Recommended total settlement: ₹{ai_analysis.get('recommended_total_settlement', 0):,.2f}."
        ),
    )

    return AISettlementAnalysisResponse(
        user_id=payload.user_id,
        financial_health=financial_health,
        settlement_results=settlement_results,
        ai_analysis=ai_analysis,
        history_id=history.history_id,
    )


# ---------------------------------------------------------------------------
# POST /ai/loan-advice
# ---------------------------------------------------------------------------


@router.post(
    "/loan-advice",
    response_model=AILoanAdviceResponse,
    summary="Personalised per-loan AI advice",
    description=(
        "Provides loan-by-loan action items, an overall financial assessment, "
        "a concrete repayment plan, and quick-win tips — powered by Gemini."
    ),
)
def ai_loan_advice(
    payload: AILoanAdviceRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AILoanAdviceResponse:
    """Generate personalised loan management advice."""
    user = _resolve_user(payload.user_id, db)

    loan_list = _loan_dicts(payload.loans)
    profile = _profile_dict(payload.financial_profile)

    if not loan_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one loan is required.",
        )

    financial_health = calculate_financial_health(payload.financial_profile, payload.loans)

    advice = generate_loan_advice(
        user_name=user.name,
        financial_profile=profile,
        loans=loan_list,
        financial_health=financial_health,
    )

    history = _save_ai_history(
        db=db,
        user_id=payload.user_id,
        negotiation_strategy=advice.get("overall_advice", ""),
        settlement_letter="",
        ai_response=(
            f"Loan advice generated for {len(loan_list)} loan(s). "
            f"AI enhanced: {advice.get('ai_enhanced', False)}."
        ),
    )

    return AILoanAdviceResponse(
        user_id=payload.user_id,
        financial_health=financial_health,
        advice=advice,
        history_id=history.history_id,
    )


# ---------------------------------------------------------------------------
# POST /ai/repayment-plan
# ---------------------------------------------------------------------------


@router.post(
    "/repayment-plan",
    response_model=AIRepaymentPlanResponse,
    summary="AI-generated debt repayment plan",
    description=(
        "Builds a step-by-step debt avalanche repayment plan using the user's "
        "monthly surplus and an optional extra monthly payment. Returns estimated "
        "months to debt-free and total interest saved."
    ),
)
def ai_repayment_plan(
    payload: AIRepaymentPlanRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AIRepaymentPlanResponse:
    """Generate an avalanche-method repayment plan."""
    user = _resolve_user(payload.user_id, db)

    loan_list = _loan_dicts(payload.loans)
    profile = _profile_dict(payload.financial_profile)

    if not loan_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one loan is required.",
        )

    financial_health = calculate_financial_health(payload.financial_profile, payload.loans)

    repayment_plan = generate_repayment_plan(
        user_name=user.name,
        financial_profile=profile,
        loans=loan_list,
        financial_health=financial_health,
        extra_monthly_payment=payload.extra_monthly_payment,
    )

    history = _save_ai_history(
        db=db,
        user_id=payload.user_id,
        negotiation_strategy=repayment_plan.get("strategy_name", "Debt Repayment Plan"),
        settlement_letter="",
        ai_response=(
            f"Repayment plan: est. {repayment_plan.get('estimated_debt_free_months', 'N/A')} month(s) to debt-free. "
            f"Monthly allocation: ₹{repayment_plan.get('monthly_allocation', 0):,.2f}."
        ),
    )

    return AIRepaymentPlanResponse(
        user_id=payload.user_id,
        financial_health=financial_health,
        repayment_plan=repayment_plan,
        history_id=history.history_id,
    )


# ---------------------------------------------------------------------------
# POST /ai/negotiation-email
# ---------------------------------------------------------------------------


@router.post(
    "/negotiation-email",
    response_model=AIEmailResponse,
    summary="Generate a professional negotiation letter to the lender",
    description=(
        "Produces a formal, personalised debt settlement letter addressed to the "
        "specific lender. Includes the proposed settlement amount, hardship context, "
        "and a request for a No Objection Certificate."
    ),
)
def ai_negotiation_email(
    payload: AIEmailRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> AIEmailResponse:
    """Generate a negotiation email / hardship letter."""
    user = _resolve_user(payload.user_id, db)

    loan = payload.loan.model_dump()
    profile = _profile_dict(payload.financial_profile)

    outstanding = loan.get("outstanding_amount", 0.0)
    settlement_pct = 0.60  # default 60%
    recommended_settlement = round(outstanding * settlement_pct, 2)

    email = generate_negotiation_email(
        user_name=user.name,
        loan_type=loan.get("loan_type", "Loan"),
        lender_name=loan.get("lender_name", "Lender"),
        outstanding_amount=outstanding,
        recommended_settlement=recommended_settlement,
        financial_profile=profile,
    )

    ai_enhanced = len(email.get("body", "")) > 300 and "Dear lender" not in email.get("body", "")

    history = _save_ai_history(
        db=db,
        user_id=payload.user_id,
        negotiation_strategy=f"Settlement letter for {loan.get('loan_type')} with {loan.get('lender_name')}",
        settlement_letter=email.get("body", ""),
        ai_response=email.get("subject", ""),
    )

    return AIEmailResponse(
        user_id=payload.user_id,
        loan_type=loan.get("loan_type", "Loan"),
        lender_name=loan.get("lender_name", "Lender"),
        outstanding_amount=outstanding,
        recommended_settlement_amount=recommended_settlement,
        subject=email.get("subject", ""),
        body=email.get("body", ""),
        ai_enhanced=ai_enhanced,
        history_id=history.history_id,
    )


# ---------------------------------------------------------------------------
# GET /ai/health
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    summary="AI engine health check",
    description="Returns whether the Gemini API key is configured and which model is active.",
)
def ai_health() -> dict:
    """Check AI engine status."""
    api_key_set = bool(os.getenv("GOOGLE_API_KEY", ""))
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return {
        "status": "operational",
        "gemini_configured": api_key_set,
        "model": model,
        "fallback_available": True,
        "endpoints": [
            "POST /ai/negotiation-strategy",
            "POST /ai/settlement-analysis",
            "POST /ai/loan-advice",
            "POST /ai/repayment-plan",
            "POST /ai/negotiation-email",
        ],
    }
