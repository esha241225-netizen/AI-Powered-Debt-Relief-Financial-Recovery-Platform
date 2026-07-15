from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.logic import calculate_financial_health, simulate_debt_timeline
from app.db.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.loan import Loan
from app.models.user import User
from app.schemas.api import DebtTimelineResponse, FinancialHealthResponse, UpdateProfileRequest, UpdateProfileResponse, TimelinePoint
from app.schemas.financial_profile import FinancialProfileRead
from app.core.auth import CurrentUser

router = APIRouter(tags=["financial-profiles"])


@router.put("/update-profile", response_model=UpdateProfileResponse)
def update_profile(payload: UpdateProfileRequest, current_user: CurrentUser, db: Session = Depends(get_db)):
	user = current_user
	payload.user_id = user.user_id

	if payload.name is not None:
		user.name = payload.name
	if payload.email is not None:
		user.email = payload.email
	if payload.password is not None:
		user.password = payload.password

	profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == payload.user_id).first()
	financial_fields = [payload.monthly_income, payload.monthly_expenses, payload.existing_debts, payload.financial_health_score]
	has_financial_update = any(field is not None for field in financial_fields)

	if profile is None and has_financial_update:
		if payload.monthly_income is None or payload.monthly_expenses is None or payload.existing_debts is None:
			raise HTTPException(status_code=400, detail="Income, expenses, and debts are required to create a financial profile")
		score = payload.financial_health_score
		if score is None:
			score, _, _ = calculate_financial_health(payload.monthly_income, payload.monthly_expenses, payload.existing_debts)
		profile = FinancialProfile(
			user_id=payload.user_id,
			monthly_income=payload.monthly_income,
			monthly_expenses=payload.monthly_expenses,
			existing_debts=payload.existing_debts,
			financial_health_score=score,
		)
		db.add(profile)
	elif profile is not None:
		if payload.monthly_income is not None:
			profile.monthly_income = payload.monthly_income
		if payload.monthly_expenses is not None:
			profile.monthly_expenses = payload.monthly_expenses
		if payload.existing_debts is not None:
			profile.existing_debts = payload.existing_debts
		if payload.financial_health_score is not None:
			profile.financial_health_score = payload.financial_health_score

		if has_financial_update and payload.financial_health_score is None:
			score, _, _ = calculate_financial_health(
				profile.monthly_income,
				profile.monthly_expenses,
				profile.existing_debts,
			)
			profile.financial_health_score = score

	db.commit()
	db.refresh(user)
	if profile is not None:
		db.refresh(profile)

	return {"message": "Profile updated successfully", "user": user, "financial_profile": profile}


@router.get("/financial-health", response_model=FinancialHealthResponse)
def financial_health(current_user: CurrentUser, db: Session = Depends(get_db)):
	user_id = current_user.user_id

	profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
	loans = db.query(Loan).filter(Loan.user_id == user_id).all()
	score, status_text, message = calculate_financial_health(
		profile.monthly_income if profile else None,
		profile.monthly_expenses if profile else None,
		profile.existing_debts if profile else None,
		sum(loan.outstanding_amount for loan in loans),
	)
	return {"user_id": user_id, "score": score, "status": status_text, "message": message}


@router.get("/debt-timeline", response_model=DebtTimelineResponse)
def debt_timeline(current_user: CurrentUser, db: Session = Depends(get_db)):
	user_id = current_user.user_id
	user = current_user

	profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
	loans = db.query(Loan).filter(Loan.user_id == user_id).all()
	total_outstanding = sum(loan.outstanding_amount for loan in loans)
	debt_timeline_report = simulate_debt_timeline(profile or user, loans)
	return {
		"user_id": user_id,
		"total_outstanding": round(total_outstanding, 2),
		"months_to_debt_free": debt_timeline_report["months_to_debt_free"],
		"final_remaining_balance": debt_timeline_report["final_remaining_balance"],
		"timeline_preview": debt_timeline_report["timeline_preview"],
	}
