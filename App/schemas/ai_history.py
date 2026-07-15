from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIHistoryBase(BaseModel):
    user_id: int
    negotiation_strategy: str
    settlement_letter: str
    ai_response: str


class AIHistoryCreate(AIHistoryBase):
    pass


class AIHistoryRead(AIHistoryBase):
    history_id: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
