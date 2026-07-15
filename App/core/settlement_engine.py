"""
settlement_engine.py
====================
Core loan & settlement processing logic for FinRelief AI.

Responsibilities
----------------
1. Calculate settlement percentage using a loan-type matrix adjusted by
   overdue months, interest rate, and EMI-to-income ratio.
2. Assign High / Medium / Low priority via a weighted scoring system.
3. Generate lender-specific negotiation letters with hardship context.
4. Produce a full settlement report dict ready for DB persistence and
   JSON serialisation.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


# ---------------------------------------------------------------------------
# Constants & lookup tables
# ---------------------------------------------------------------------------

# Base settlement % by loan type (key: lower-cased type, value: (base, overdue_tiers))
# overdue_tiers = [0 months, 1-3 months, 4-6 months, 7+ months]
_SETTLEMENT_TABLE: dict[str, list[float]] = {
    "credit card":     [45.0, 55.0, 65.0, 72.0],
    "personal loan":   [50.0, 58.0, 65.0, 70.0],
    "home loan":       [40.0, 48.0, 55.0, 62.0],
    "auto loan":       [48.0, 55.0, 62.0, 68.0],
    "car loan":        [48.0, 55.0, 62.0, 68.0],
    "education loan":  [42.0, 50.0, 58.0, 65.0],
    "student loan":    [42.0, 50.0, 58.0, 65.0],
    "business loan":   [52.0, 60.0, 67.0, 73.0],
    "gold loan":       [38.0, 45.0, 52.0, 58.0],
    "mortgage":        [40.0, 48.0, 55.0, 62.0],
}

_DEFAULT_TIERS: list[float] = [50.0, 58.0, 65.0, 70.0]

_SETTLEMENT_MIN = 40.0
_SETTLEMENT_MAX = 75.0

# Priority scoring weights
_PRIORITY_HIGH_THRESHOLD = 55
_PRIORITY_MEDIUM_THRESHOLD = 25

# Lender category keywords for letter tone
_BANK_KEYWORDS = {"bank", "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "canara", "ubi", "bob"}
_NBFC_KEYWORDS = {"finance", "capital", "credit", "lending", "fintech", "bajaj", "tata", "mahindra"}
_CARD_KEYWORDS = {"card", "amex", "visa", "mastercard", "rupay"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _overdue_tier(overdue_months: int) -> int:
    """Map overdue months to a tier index (0–3)."""
    if overdue_months <= 0:
        return 0
    if overdue_months <= 3:
        return 1
    if overdue_months <= 6:
        return 2
    return 3


def _lender_category(lender_name: str) -> str:
    """Classify lender as 'bank', 'nbfc', 'card', or 'lender'."""
    lower = lender_name.lower()
    if any(k in lower for k in _CARD_KEYWORDS):
        return "card"
    if any(k in lower for k in _BANK_KEYWORDS):
        return "bank"
    if any(k in lower for k in _NBFC_KEYWORDS):
        return "nbfc"
    return "lender"


# ---------------------------------------------------------------------------
# 1. Settlement percentage calculator
# ---------------------------------------------------------------------------

def calculate_settlement_percentage(
    loan_type: str,
    outstanding_amount: float,
    overdue_months: int,
    interest_rate: float,
    emi_ratio_percent: float = 0.0,
    debt_to_income_percent: float = 0.0,
) -> float:
    """Return the recommended settlement percentage (40–75%).

    Algorithm
    ---------
    1. Look up base % from the loan-type matrix using the overdue tier.
    2. Add modifiers for high interest rate, EMI ratio, and debt-to-income.
    3. Clamp result to [_SETTLEMENT_MIN, _SETTLEMENT_MAX].
    """
    tiers = _SETTLEMENT_TABLE.get(loan_type.strip().lower(), _DEFAULT_TIERS)
    base_pct = tiers[_overdue_tier(overdue_months)]

    modifier = 0.0
    if interest_rate > 24:
        modifier += 5.0
    elif interest_rate > 18:
        modifier += 3.0
    elif interest_rate > 12:
        modifier += 1.5

    if emi_ratio_percent > 60:
        modifier += 5.0
    elif emi_ratio_percent > 50:
        modifier += 3.0

    if debt_to_income_percent > 100:
        modifier += 4.0
    elif debt_to_income_percent > 80:
        modifier += 2.0

    result = base_pct + modifier
    return round(max(_SETTLEMENT_MIN, min(_SETTLEMENT_MAX, result)), 2)


# ---------------------------------------------------------------------------
# 2. Priority engine
# ---------------------------------------------------------------------------

def calculate_priority(
    overdue_months: int,
    interest_rate: float,
    outstanding_amount: float,
    emi_ratio_percent: float = 0.0,
) -> tuple[str, int]:
    """Return (priority_label, score) using a weighted scoring system.

    Scoring matrix
    --------------
    Overdue > 0 months       : +40 pts
    Overdue > 3 months       : +20 pts additional
    Interest rate > 24%      : +30 pts
    Interest rate > 18%      : +20 pts
    Interest rate > 12%      : +10 pts
    Outstanding > 1,000,000  : +15 pts
    Outstanding > 500,000    : +10 pts
    EMI ratio > 60%          : +15 pts
    EMI ratio > 50%          : +10 pts

    Thresholds
    ----------
    score >= 55  →  High
    score >= 25  →  Medium
    score <  25  →  Low
    """
    score = 0

    if overdue_months > 0:
        score += 40
    if overdue_months > 3:
        score += 20

    if interest_rate > 24:
        score += 30
    elif interest_rate > 18:
        score += 20
    elif interest_rate > 12:
        score += 10

    if outstanding_amount > 1_000_000:
        score += 15
    elif outstanding_amount > 500_000:
        score += 10

    if emi_ratio_percent > 60:
        score += 15
    elif emi_ratio_percent > 50:
        score += 10

    if score >= _PRIORITY_HIGH_THRESHOLD:
        label = "High"
    elif score >= _PRIORITY_MEDIUM_THRESHOLD:
        label = "Medium"
    else:
        label = "Low"

    return label, score


# ---------------------------------------------------------------------------
# 3. Negotiation letter generator
# ---------------------------------------------------------------------------

_LETTER_HEADER = "TO WHOM IT MAY CONCERN"

def generate_negotiation_letter(
    borrower_name: str,
    lender_name: str,
    loan_type: str,
    outstanding_amount: float,
    recommended_settlement: float,
    settlement_percentage: float,
    monthly_income: float,
    monthly_expenses: float,
    overdue_months: int,
    interest_rate: float,
    today: date | None = None,
) -> str:
    """Generate a professional, lender-specific hardship & settlement letter.

    The letter is tailored by lender category (bank / NBFC / card issuer)
    and adjusts its tone and legal references accordingly.
    """
    today = today or date.today()
    date_str = today.strftime("%d %B %Y")
    category = _lender_category(lender_name)
    surplus = monthly_income - monthly_expenses
    savings_vs_full = outstanding_amount - recommended_settlement

    # --- Lender-specific opening address block ---
    if category == "bank":
        dept = "Retail Loans Recovery Department"
        ref_law = "RBI's Guidelines on Settlement of NPAs (Circular No. RBI/2023-24/73)"
        closing_note = (
            "I request that this settlement be reflected in my credit bureau report as "
            "'Settled' and that a formal No Objection Certificate (NOC) be issued within "
            "7 working days of the settlement payment being received by the bank."
        )
    elif category == "nbfc":
        dept = "Collections & Recovery Team"
        ref_law = "RBI's Fair Practices Code for NBFCs"
        closing_note = (
            "Kindly provide written confirmation of this offer's acceptance, waive all "
            "penal interest and foreclosure charges, and issue a No Objection Certificate "
            "(NOC) upon receipt of the agreed settlement amount."
        )
    elif category == "card":
        dept = "Credit Card Collections Department"
        ref_law = "RBI's Master Circular on Credit Card Operations"
        closing_note = (
            "Upon acceptance, I request the card account be closed, all outstanding interest "
            "and late fees be waived, and a No Objection Certificate (NOC) be issued "
            "confirming full and final settlement."
        )
    else:
        dept = "Loans Recovery Department"
        ref_law = "applicable RBI settlement guidelines"
        closing_note = (
            "Please provide written acceptance and issue a No Objection Certificate (NOC) "
            "upon receipt of the settlement amount."
        )

    # --- Hardship context paragraph ---
    hardship_para = (
        f"I am writing to formally request a one-time full and final settlement of my "
        f"{loan_type} account with {lender_name}. Due to unforeseen financial hardship, "
        f"I am currently unable to service this loan at the original contractual terms."
    )
    if overdue_months > 0:
        hardship_para += (
            f" The account has been overdue for {overdue_months} month(s), during which time "
            f"I have been actively seeking a resolution. The accumulation of penal interest "
            f"at {interest_rate:.2f}% p.a. has significantly increased my debt burden."
        )

    # --- Financial position paragraph ---
    financial_para = (
        f"My current monthly income is INR {monthly_income:,.2f} against monthly living expenses "
        f"of INR {monthly_expenses:,.2f}, leaving a net surplus of INR {surplus:,.2f}. After meeting "
        f"essential obligations, I am unable to sustain the full outstanding liability of "
        f"INR {outstanding_amount:,.2f}."
    )

    # --- Proposal paragraph ---
    proposal_para = (
        f"After careful review of my financial position and in reference to {ref_law}, "
        f"I propose a lump-sum settlement of INR {recommended_settlement:,.2f} — representing "
        f"{settlement_percentage:.1f}% of the total outstanding balance. This would save your "
        f"institution the cost of prolonged recovery efforts while allowing me to resolve "
        f"this liability in full. The settlement amount of INR {recommended_settlement:,.2f} "
        f"would be paid within 10 working days of receiving written acceptance of this offer, "
        f"thereby saving INR {savings_vs_full:,.2f} compared to the full outstanding amount."
    )

    # --- Assemble letter ---
    letter = f"""Date: {date_str}

To,
The Manager / {dept}
{lender_name}

Subject: Request for One-Time Settlement — {loan_type} Account

Dear Sir / Madam,

{hardship_para}

{financial_para}

{proposal_para}

I sincerely request your organisation to consider this settlement proposal in a humanitarian spirit. {closing_note}

I am available for a discussion at your earliest convenience to finalise the terms.

Thanking you,

Yours faithfully,
{borrower_name}

Enclosures:
1. Proof of Income (Salary Slips / Bank Statements)
2. Proof of Existing Liabilities
3. Recent Bank Statements (last 3 months)"""

    return letter.strip()


# ---------------------------------------------------------------------------
# 4. Full settlement report builder
# ---------------------------------------------------------------------------

def build_settlement_report(
    user_name: str,
    loans: list[Any],
    monthly_income: float,
    monthly_expenses: float,
    existing_debts: float = 0.0,
) -> dict[str, Any]:
    """Build a complete settlement report for all loans.

    Each loan object must have these attributes (or dict keys):
        loan_id, loan_type, lender_name, outstanding_amount,
        interest_rate, overdue_months, emi (optional)

    Returns a dict with:
        total_emi, total_outstanding, surplus, emi_ratio_percent,
        debt_to_income_percent, settlement_results (list of per-loan dicts)
    """
    def _get(obj: Any, *keys: str, default: Any = None) -> Any:
        for key in keys:
            val = getattr(obj, key, None) if not isinstance(obj, dict) else obj.get(key)
            if val is not None:
                return val
        return default

    loan_list = list(loans)

    # --- Portfolio aggregates ---
    total_outstanding = sum(
        _safe_float(_get(ln, "outstanding_amount")) for ln in loan_list
    )
    total_emi = sum(
        _safe_float(_get(ln, "emi", default=0.0)) for ln in loan_list
    )
    surplus = monthly_income - monthly_expenses - total_emi

    emi_ratio = (total_emi / monthly_income * 100) if monthly_income > 0 else 0.0
    debt_to_income = (total_outstanding / monthly_income * 100) if monthly_income > 0 else 0.0

    # --- Per-loan settlement results ---
    results: list[dict[str, Any]] = []

    for loan in loan_list:
        loan_id = _get(loan, "loan_id", "id")
        loan_type = str(_get(loan, "loan_type", default="Personal Loan"))
        lender_name = str(_get(loan, "lender_name", default="Unknown Lender"))
        outstanding = _safe_float(_get(loan, "outstanding_amount"))
        interest_rate = _safe_float(_get(loan, "interest_rate"))
        overdue_months = int(_safe_float(_get(loan, "overdue_months", default=0)))
        loan_amount = _safe_float(_get(loan, "loan_amount", default=outstanding))
        emi = _safe_float(_get(loan, "emi", default=0.0))

        # Settlement percentage (loan-type matrix + modifiers)
        settlement_pct = calculate_settlement_percentage(
            loan_type=loan_type,
            outstanding_amount=outstanding,
            overdue_months=overdue_months,
            interest_rate=interest_rate,
            emi_ratio_percent=emi_ratio,
            debt_to_income_percent=debt_to_income,
        )
        recommended_amount = round(outstanding * settlement_pct / 100, 2)

        # Priority (weighted score)
        priority, priority_score = calculate_priority(
            overdue_months=overdue_months,
            interest_rate=interest_rate,
            outstanding_amount=outstanding,
            emi_ratio_percent=emi_ratio,
        )

        # Risk category mirrors priority for backward compatibility
        risk_category = priority
        risk_score = priority_score

        # Negotiation letter
        letter = generate_negotiation_letter(
            borrower_name=user_name,
            lender_name=lender_name,
            loan_type=loan_type,
            outstanding_amount=outstanding,
            recommended_settlement=recommended_amount,
            settlement_percentage=settlement_pct,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            overdue_months=overdue_months,
            interest_rate=interest_rate,
        )

        # Settlement prediction label
        if settlement_pct >= 65:
            prediction = "Low settlement potential — significant recovery expected"
        elif settlement_pct >= 55:
            prediction = "Moderate settlement potential — negotiation recommended"
        else:
            prediction = "High settlement potential — lender likely to accept"

        results.append({
            "loan_id": loan_id,
            "loan_type": loan_type,
            "lender_name": lender_name,
            "loan_amount": round(loan_amount, 2),
            "outstanding_amount": round(outstanding, 2),
            "interest_rate": round(interest_rate, 2),
            "overdue_months": overdue_months,
            "emi": round(emi, 2),
            "settlement_percentage": settlement_pct,
            "recommended_settlement_amount": recommended_amount,
            "settlement_prediction": prediction,
            "priority": priority,
            "priority_score": priority_score,
            "risk_category": risk_category,
            "risk_score": risk_score,
            "suggested_settlement_percentage": settlement_pct,  # backward compat alias
            "negotiation_letter": letter,
        })

    # Sort: High → Medium → Low, then highest outstanding first
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    results.sort(key=lambda r: (priority_order[r["priority"]], -r["outstanding_amount"]))

    return {
        "total_emi": round(total_emi, 2),
        "total_outstanding": round(total_outstanding, 2),
        "surplus": round(surplus, 2),
        "emi_ratio_percent": round(emi_ratio, 2),
        "debt_to_income_percent": round(debt_to_income, 2),
        "settlement_results": results,
    }
