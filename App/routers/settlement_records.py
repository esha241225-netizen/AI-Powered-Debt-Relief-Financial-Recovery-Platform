"""
routers/settlement_records.py
==============================
Settlement processing endpoints — calculates settlement percentage based on
overdue months and loan type, assigns priority, generates negotiation letters,
and persists everything to the settlement_records table.

Endpoints
---------
GET    /settlement-predictor              — run full settlement analysis for all user loans
POST   /settlement-records/manual         — store a manually specified settlement record
GET    /settlement-records/{id}           — fetch a single settlement record
GET    /settlement-records/{id}/letter    — retrieve the negotiation letter as plain text
DELETE /settlement-records/{id}           — delete a settlement record
GET    /settlement-records                — list records (all or by user_id)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.settlement_engine import build_settlement_report, generate_negotiation_letter
from app.db.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.loan import Loan
from app.models.settlement_record import SettlementRecord
from app.models.user import User
from app.schemas.api import (
    ManualSettlementRequest,
    NegotiationLetterResponse,
    SettlementPredictionResponse,
)
from app.schemas.settlement_record import SettlementRecordCreate, SettlementRecordRead
from app.core.auth import CurrentUser

router = APIRouter(tags=["settlement-records"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_or_404(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")
    return user


def _get_record_or_404(settlement_id: int, db: Session) -> SettlementRecord:
    record = db.get(SettlementRecord, settlement_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement record {settlement_id} not found",
        )
    return record


# ---------------------------------------------------------------------------
# GET /settlement-predictor
# ---------------------------------------------------------------------------

@router.get(
    "/settlement-predictor",
    response_model=SettlementPredictionResponse,
    summary="Run full settlement analysis for all user loans",
    description=(
        "Calculates settlement percentage (using loan-type matrix + overdue months), "
        "assigns High/Medium/Low priority via weighted scoring, generates a "
        "lender-specific negotiation letter for every loan, and persists all "
        "results to the settlement_records table."
    ),
)
def settlement_predictor(current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    user_id = current_user.user_id
    user = current_user
    profile = (
        db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    )
    loans = db.query(Loan).filter(Loan.user_id == user_id).all()

    if not loans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No loans found for user")

    monthly_income = profile.monthly_income if profile else 0.0
    monthly_expenses = profile.monthly_expenses if profile else 0.0
    existing_debts = profile.existing_debts if profile else 0.0

    # Run the settlement engine
    report = build_settlement_report(
        user_name=user.name,
        loans=loans,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        existing_debts=existing_debts,
    )

    # Wipe old records for this user and replace with fresh results
    db.query(SettlementRecord).filter(SettlementRecord.user_id == user_id).delete(
        synchronize_session=False
    )

    for item in report["settlement_results"]:
        record = SettlementRecord(
            user_id=user_id,
            loan_id=item["loan_id"],
            loan_type=item["loan_type"],
            lender_name=item["lender_name"],
            settlement_percentage=item["settlement_percentage"],
            settlement_prediction=(
                f'{item["priority"]} priority — {item["settlement_percentage"]:.1f}% settlement'
            ),
            recommended_amount=item["recommended_settlement_amount"],
            priority_level=item["priority"],
            negotiation_letter=item["negotiation_letter"],
        )
        db.add(record)

    db.commit()

    return {"user_id": user_id, **report}


# ---------------------------------------------------------------------------
# POST /settlement-records/manual
# ---------------------------------------------------------------------------

@router.post(
    "/settlement-records/manual",
    response_model=SettlementRecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Manually create a settlement record",
    description="Store a settlement record with custom percentage and an optional letter.",
)
def create_manual_settlement(
    payload: ManualSettlementRequest, current_user: CurrentUser, db: Session = Depends(get_db)
) -> SettlementRecord:
    payload.user_id = current_user.user_id
    _get_user_or_404(payload.user_id, db)
    loan = db.get(Loan, payload.loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan {payload.loan_id} not found")
    if loan.user_id != payload.user_id:
        raise HTTPException(status_code=403, detail="Loan does not belong to this user")

    # Auto-generate letter if not supplied
    letter = payload.negotiation_letter
    if not letter:
        profile = (
            db.query(FinancialProfile)
            .filter(FinancialProfile.user_id == payload.user_id)
            .first()
        )
        user = db.get(User, payload.user_id)
        letter = generate_negotiation_letter(
            borrower_name=user.name,
            lender_name=loan.lender_name,
            loan_type=loan.loan_type,
            outstanding_amount=loan.outstanding_amount,
            recommended_settlement=payload.recommended_amount,
            settlement_percentage=payload.settlement_percentage,
            monthly_income=profile.monthly_income if profile else 0.0,
            monthly_expenses=profile.monthly_expenses if profile else 0.0,
            overdue_months=loan.overdue_months,
            interest_rate=loan.interest_rate,
        )

    record = SettlementRecord(
        user_id=payload.user_id,
        loan_id=payload.loan_id,
        loan_type=loan.loan_type,
        lender_name=loan.lender_name,
        settlement_percentage=payload.settlement_percentage,
        settlement_prediction=f"Manual — {payload.settlement_percentage:.1f}%",
        recommended_amount=payload.recommended_amount,
        priority_level=payload.priority_level,
        negotiation_letter=letter,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# GET /settlement-records
# ---------------------------------------------------------------------------

@router.get(
    "/settlement-records",
    response_model=list[SettlementRecordRead],
    summary="List all settlement records (optionally filter by user_id)",
)
def list_settlement_records(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> list[SettlementRecord]:
    user_id = current_user.user_id
    query = db.query(SettlementRecord)
    if user_id is not None:
        query = query.filter(SettlementRecord.user_id == user_id)
    return query.order_by(SettlementRecord.created_at.desc()).all()


# ---------------------------------------------------------------------------
# GET /settlement-records/{settlement_id}
# ---------------------------------------------------------------------------

@router.get(
    "/settlement-records/{settlement_id}",
    response_model=SettlementRecordRead,
    summary="Retrieve a single settlement record by ID",
)
def get_settlement_record(settlement_id: int, db: Session = Depends(get_db)) -> SettlementRecord:
    return _get_record_or_404(settlement_id, db)


# ---------------------------------------------------------------------------
# GET /settlement-records/{settlement_id}/letter
# ---------------------------------------------------------------------------

@router.get(
    "/settlement-records/{settlement_id}/letter",
    response_model=NegotiationLetterResponse,
    summary="Retrieve negotiation letter for a settlement record",
    description=(
        "Returns the full negotiation letter stored in the settlement record. "
        "The letter is lender-specific and includes the borrower's hardship context, "
        "proposed settlement amount, and NOC request."
    ),
)
def get_negotiation_letter(
    settlement_id: int, db: Session = Depends(get_db)
) -> dict:
    record = _get_record_or_404(settlement_id, db)
    return {
        "settlement_id": record.settlement_id,
        "loan_id": record.loan_id,
        "loan_type": record.loan_type,
        "lender_name": record.lender_name,
        "settlement_percentage": record.settlement_percentage,
        "recommended_amount": record.recommended_amount,
        "priority_level": record.priority_level,
        "negotiation_letter": record.negotiation_letter,
        "created_at": record.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /settlement-records/{settlement_id}/letter/text
# ---------------------------------------------------------------------------

@router.get(
    "/settlement-records/{settlement_id}/letter/text",
    summary="Download negotiation letter as plain text",
    response_class=Response,
)
def download_negotiation_letter(
    settlement_id: int, db: Session = Depends(get_db)
) -> Response:
    """Return the letter body as a plain-text download."""
    record = _get_record_or_404(settlement_id, db)
    filename = f"negotiation_letter_{settlement_id}.txt"
    return Response(
        content=record.negotiation_letter,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# DELETE /settlement-records/{settlement_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/settlement-records/{settlement_id}",
    summary="Delete a settlement record",
)
def delete_settlement_record(settlement_id: int, db: Session = Depends(get_db)) -> dict:
    record = _get_record_or_404(settlement_id, db)
    db.delete(record)
    db.commit()
    return {"message": "Settlement record deleted", "settlement_id": settlement_id}
