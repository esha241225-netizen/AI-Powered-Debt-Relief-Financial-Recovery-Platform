"""
routers/loans.py
================
CRUD endpoints for loan records with SQLAlchemy ORM storage/retrieval,
per-loan priority scoring, and portfolio summary aggregation.

Endpoints
---------
POST   /add-loan                    — create a new loan
GET    /loans                       — list loans (all or by user_id)
GET    /loans/{loan_id}             — fetch a single loan
PUT    /loans/{loan_id}             — partial update (outstanding, overdue, EMI, etc.)
DELETE /delete-loan/{loan_id}       — delete a loan
GET    /loans/{loan_id}/priority    — settlement % + priority for one loan
GET    /loans/summary/{user_id}     — portfolio-level aggregates
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.settlement_engine import (
    build_settlement_report,
    calculate_priority,
    calculate_settlement_percentage,
)
from app.db.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.loan import Loan
from app.models.user import User
from app.schemas.api import LoanPortfolioSummary
from app.schemas.loan import LoanCreate, LoanPriority, LoanRead, LoanUpdate

router = APIRouter(tags=["loans"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_loan_or_404(loan_id: int, db: Session) -> Loan:
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Loan {loan_id} not found")
    return loan


def _get_user_or_404(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return user


def _emi_ratio(loans: list[Loan], monthly_income: float) -> float:
    if monthly_income <= 0:
        return 0.0
    total_emi = sum(ln.emi or 0.0 for ln in loans)
    return (total_emi / monthly_income) * 100


# ---------------------------------------------------------------------------
# POST /add-loan
# ---------------------------------------------------------------------------

@router.post(
    "/add-loan",
    response_model=LoanRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new loan record",
    description=(
        "Stores a loan record via SQLAlchemy ORM. "
        "Provide `overdue_months` and `lender_name` for accurate settlement and priority calculations."
    ),
)
def add_loan(
    payload: LoanCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Loan:
    # Enforce ownership — users can only add loans to their own account
    if payload.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot add loans for another user")
    loan = Loan(**payload.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


# ---------------------------------------------------------------------------
# GET /loans
# ---------------------------------------------------------------------------

@router.get(
    "/loans",
    response_model=list[LoanRead],
    summary="List the current user's loans",
)
def get_loans(current_user: CurrentUser, db: Session = Depends(get_db)) -> list[Loan]:
    # Indexed FK query — returns only loans belonging to the authenticated user
    return db.query(Loan).filter(Loan.user_id == current_user.user_id).all()


# ---------------------------------------------------------------------------
# GET /loans/{loan_id}
# ---------------------------------------------------------------------------

@router.get(
    "/loans/{loan_id}",
    response_model=LoanRead,
    summary="Retrieve a single loan record by ID",
)
def get_loan(loan_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> Loan:
    loan = _get_loan_or_404(loan_id, db)
    if loan.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return loan


# ---------------------------------------------------------------------------
# PUT /loans/{loan_id}
# ---------------------------------------------------------------------------

@router.put(
    "/loans/{loan_id}",
    response_model=LoanRead,
    summary="Partially update a loan record",
    description=(
        "Update any subset of loan fields — e.g. mark a loan overdue by setting "
        "`overdue_months`, update `outstanding_amount` after a payment, or set the `emi`."
    ),
)
def update_loan(
    loan_id: int,
    payload: LoanUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Loan:
    loan = _get_loan_or_404(loan_id, db)
    if loan.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loan, field, value)
    db.commit()
    db.refresh(loan)
    return loan


# ---------------------------------------------------------------------------
# DELETE /delete-loan/{loan_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/delete-loan/{loan_id}",
    summary="Delete a loan and all its settlement records",
)
def delete_loan(loan_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    loan = _get_loan_or_404(loan_id, db)
    if loan.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    db.delete(loan)
    db.commit()
    return {"message": "Loan deleted successfully", "loan_id": loan_id}


# ---------------------------------------------------------------------------
# GET /loans/{loan_id}/priority
# ---------------------------------------------------------------------------

@router.get(
    "/loans/{loan_id}/priority",
    response_model=LoanPriority,
    summary="Get settlement percentage and priority for a single loan",
    description=(
        "Runs the settlement-percentage matrix and weighted priority scorer "
        "for a single loan in isolation."
    ),
)
def get_loan_priority(loan_id: int, current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    loan = _get_loan_or_404(loan_id, db)
    if loan.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Get the user's financial profile for EMI ratio
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == loan.user_id)
        .first()
    )
    monthly_income = profile.monthly_income if profile else 0.0
    user_loans = db.query(Loan).filter(Loan.user_id == loan.user_id).all()
    emi_ratio = _emi_ratio(user_loans, monthly_income)

    settlement_pct = calculate_settlement_percentage(
        loan_type=loan.loan_type,
        outstanding_amount=loan.outstanding_amount,
        overdue_months=loan.overdue_months,
        interest_rate=loan.interest_rate,
        emi_ratio_percent=emi_ratio,
    )
    priority, priority_score = calculate_priority(
        overdue_months=loan.overdue_months,
        interest_rate=loan.interest_rate,
        outstanding_amount=loan.outstanding_amount,
        emi_ratio_percent=emi_ratio,
    )

    if settlement_pct >= 65:
        prediction = "Low settlement potential — significant recovery expected"
    elif settlement_pct >= 55:
        prediction = "Moderate settlement potential — negotiation recommended"
    else:
        prediction = "High settlement potential — lender likely to accept"

    return {
        "loan_id": loan.loan_id,
        "loan_type": loan.loan_type,
        "lender_name": loan.lender_name,
        "outstanding_amount": loan.outstanding_amount,
        "interest_rate": loan.interest_rate,
        "overdue_months": loan.overdue_months,
        "settlement_percentage": settlement_pct,
        "recommended_settlement_amount": round(loan.outstanding_amount * settlement_pct / 100, 2),
        "priority": priority,
        "priority_score": priority_score,
        "settlement_prediction": prediction,
    }


# ---------------------------------------------------------------------------
# GET /loans/summary/{user_id}
# ---------------------------------------------------------------------------

@router.get(
    "/loans/summary/{user_id}",
    response_model=LoanPortfolioSummary,
    summary="Aggregated portfolio-level summary for the authenticated user",
)
def get_loan_summary(current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    user_id = current_user.user_id
    profile = (
        db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    )
    monthly_income = profile.monthly_income if profile else 0.0
    loans = db.query(Loan).filter(Loan.user_id == user_id).all()

    total_loan_amount = sum(ln.loan_amount for ln in loans)
    total_outstanding = sum(ln.outstanding_amount for ln in loans)
    total_emi = sum(ln.emi or 0.0 for ln in loans)
    overdue_loans = sum(1 for ln in loans if ln.overdue_months > 0)

    emi_ratio = (total_emi / monthly_income * 100) if monthly_income > 0 else 0.0
    debt_to_income = (total_outstanding / monthly_income * 100) if monthly_income > 0 else 0.0

    # Assign priority per loan and count
    high = medium = low = 0
    for ln in loans:
        priority, _ = calculate_priority(
            overdue_months=ln.overdue_months,
            interest_rate=ln.interest_rate,
            outstanding_amount=ln.outstanding_amount,
            emi_ratio_percent=emi_ratio,
        )
        if priority == "High":
            high += 1
        elif priority == "Medium":
            medium += 1
        else:
            low += 1

    stress_level = (
        "High" if emi_ratio > 50 else ("Medium" if emi_ratio >= 30 else "Low")
    )

    return {
        "user_id": user_id,
        "total_loans": len(loans),
        "total_loan_amount": round(total_loan_amount, 2),
        "total_outstanding": round(total_outstanding, 2),
        "total_emi": round(total_emi, 2),
        "overdue_loans": overdue_loans,
        "high_priority_loans": high,
        "medium_priority_loans": medium,
        "low_priority_loans": low,
        "emi_ratio_percent": round(emi_ratio, 2),
        "debt_to_income_percent": round(debt_to_income, 2),
        "stress_level": stress_level,
    }
