from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logic import calculate_financial_health, calculate_loan_priority
from app.db.session import get_db
from app.models.ai_history import AIHistory
from app.models.financial_profile import FinancialProfile
from app.models.loan import Loan
from app.models.settlement_record import SettlementRecord
from app.models.user import User
from app.schemas.api import DashboardDataResponse, LoginRequest, LoginResponse
from app.schemas.api import DashboardSummary
from app.schemas.api import FinancialHealthResponse
from app.schemas.user import UserCreate, UserRead
from app.core.auth import CurrentUser

router = APIRouter(tags=["users"])





@router.get("/dashboard-data", response_model=DashboardDataResponse)
def dashboard_data(current_user: CurrentUser, db: Session = Depends(get_db)):
	user_id = current_user.user_id
	user = current_user

	financial_profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
	loans = db.query(Loan).filter(Loan.user_id == user_id).all()
	settlement_records = db.query(SettlementRecord).filter(SettlementRecord.user_id == user_id).all()
	ai_history = db.query(AIHistory).filter(AIHistory.user_id == user_id).all()

	outstanding_total = sum(loan.outstanding_amount for loan in loans)
	loan_priority_report = calculate_loan_priority(loans, emi_ratio=0)
	score, status_text, message = calculate_financial_health(
		financial_profile.monthly_income if financial_profile else None,
		financial_profile.monthly_expenses if financial_profile else None,
		financial_profile.existing_debts if financial_profile else None,
		outstanding_total,
	)

	return {
		"user": user,
		"financial_profile": financial_profile,
		"loans": loans,
		"loan_priorities": loan_priority_report,
		"settlement_records": settlement_records,
		"ai_history": ai_history,
		"summary": {
			"total_loans": len(loans),
			"total_outstanding": round(outstanding_total, 2),
			"settlement_records": len(settlement_records),
			"ai_history": len(ai_history),
			"financial_health_score": score,
			"financial_health_status": status_text,
		},
	}
