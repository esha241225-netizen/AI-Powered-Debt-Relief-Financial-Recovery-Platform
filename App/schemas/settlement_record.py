from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SettlementRecordBase(BaseModel):
    user_id: int
    loan_id: int
    loan_type: str = ""
    lender_name: str = ""
    settlement_percentage: float = 0.0
    settlement_prediction: str
    recommended_amount: float
    priority_level: str
    negotiation_letter: str = ""


class SettlementRecordCreate(SettlementRecordBase):
    pass


class SettlementRecordRead(SettlementRecordBase):
    settlement_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
