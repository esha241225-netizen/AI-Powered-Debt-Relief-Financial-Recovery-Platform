from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.ai_engine import generate_negotiation_strategy, generate_negotiation_email
from app.core.logic import calculate_financial_health
from app.db.session import get_db
from app.models.ai_history import AIHistory
from app.models.financial_profile import FinancialProfile
from app.models.loan import Loan
from app.models.user import User
from app.schemas.api import NegotiationEmailResponse, NegotiationStrategyResponse
from app.schemas.ai_history import AIHistoryRead

router = APIRouter(tags=["ai-history"])


@router.get("/ai-negotiation-strategy", response_model=NegotiationStrategyResponse)
def ai_negotiation_strategy(loan_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
	user_id = current_user.user_id
	user = current_user
	loan = db.get(Loan, loan_id)
	if not loan or loan.user_id != user_id:
		raise HTTPException(status_code=404, detail="Loan not found")

	profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
	score, status_text, _ = calculate_financial_health(
		profile.monthly_income if profile else None,
		profile.monthly_expenses if profile else None,
		profile.existing_debts if profile else None,
		loan.outstanding_amount,
	)
	profile_dict = {
		"monthly_income": profile.monthly_income if profile else 0.0,
		"monthly_expenses": profile.monthly_expenses if profile else 0.0,
		"existing_debts": profile.existing_debts if profile else 0.0,
		"financial_health_score": 0.0
	}
	loan_dict = {
		"loan_id": loan.loan_id,
		"loan_type": loan.loan_type,
		"lender_name": loan.lender_name,
		"outstanding_amount": loan.outstanding_amount,
		"interest_rate": loan.interest_rate,
		"overdue_months": loan.overdue_months,
		"due_date": loan.due_date.isoformat() if loan.due_date else "",
		"emi": loan.emi
	}
	health_data = {
		"stress_level": status_text,
		"emi_ratio_percent": (loan.emi / profile_dict["monthly_income"] * 100) if profile_dict["monthly_income"] else 0.0,
		"debt_to_income_percent": (loan.outstanding_amount / profile_dict["monthly_income"] * 100) if profile_dict["monthly_income"] else 0.0,
		"surplus": profile_dict["monthly_income"] - profile_dict["monthly_expenses"] - (loan.emi or 0),
		"total_outstanding": loan.outstanding_amount
	}

	strategy = generate_negotiation_strategy(
		user_name=user.name,
		financial_profile=profile_dict,
		loans=[loan_dict],
		financial_health=health_data,
		settlement_data={}
	)

	history = AIHistory(
		user_id=user_id,
		negotiation_strategy=strategy,
		settlement_letter="",
		ai_response="Gemini-generated negotiation strategy",
	)
	db.add(history)
	db.commit()
	db.refresh(history)
	return {"history_id": history.history_id, "user_id": user_id, "loan_id": loan_id, "negotiation_strategy": strategy}


@router.get("/generate-negotiation-email/{loan_id}", response_model=NegotiationEmailResponse)
def generate_negotiation_email(loan_id: int, current_user: CurrentUser, db: Session = Depends(get_db)):
	user_id = current_user.user_id
	user = current_user
	loan = db.get(Loan, loan_id)
	if not loan or loan.user_id != user_id:
		raise HTTPException(status_code=404, detail="Loan not found")

	profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
	profile_dict = {
		"monthly_income": profile.monthly_income if profile else 0.0,
		"monthly_expenses": profile.monthly_expenses if profile else 0.0,
		"existing_debts": profile.existing_debts if profile else 0.0,
		"financial_health_score": 0.0
	}

	recommended_amount = round(loan.outstanding_amount * 0.6, 2)
	email = generate_negotiation_email(
		user_name=user.name,
		loan_type=loan.loan_type,
		lender_name=loan.lender_name,
		outstanding_amount=loan.outstanding_amount,
		recommended_settlement=recommended_amount,
		financial_profile=profile_dict,
	)

	subject = email.get("subject", "Settlement request")
	body = email.get("body", "")

	history = AIHistory(
		user_id=user_id,
		negotiation_strategy="",
		settlement_letter=body,
		ai_response=subject,
	)
	db.add(history)
	db.commit()
	db.refresh(history)
	return {"history_id": history.history_id, "user_id": user_id, "loan_id": loan_id, "subject": subject, "body": body}


@router.get("/ai-history", response_model=list[AIHistoryRead])
def ai_history(current_user: CurrentUser, db: Session = Depends(get_db)):
	# Returns only the authenticated user's AI history logs
	return db.query(AIHistory).filter(AIHistory.user_id == current_user.user_id).order_by(AIHistory.generated_at.desc()).all()

