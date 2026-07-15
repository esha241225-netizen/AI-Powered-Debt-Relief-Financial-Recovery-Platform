from app.db.session import Base, engine
from app.models import AIHistory, FinancialProfile, Loan, SettlementRecord, User  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
