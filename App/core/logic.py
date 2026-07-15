import importlib
import json
import os
from datetime import date
from datetime import datetime

from dotenv import load_dotenv


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API if key is available, otherwise use rule-based fallback."""
    if not GOOGLE_API_KEY:
        return None  # Will fall through to fallback

    try:
        genai = importlib.import_module("google.generativeai")
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _month_delta(later: date, earlier: date) -> int:
    months = (later.year - earlier.year) * 12 + (later.month - earlier.month)
    if later.day < earlier.day:
        months -= 1
    return max(months, 0)


def _loan_id(loan: object) -> object:
    return getattr(loan, "id", getattr(loan, "loan_id", None))


def _loan_lender_name(loan: object) -> str:
    return str(getattr(loan, "lender_name", getattr(loan, "loan_type", "Unknown Lender")))


def _loan_outstanding_amount(loan: object) -> float:
    return _safe_float(getattr(loan, "outstanding_amount", getattr(loan, "balance", getattr(loan, "loan_amount", 0.0))))


def _loan_interest_rate(loan: object) -> float:
    return _safe_float(getattr(loan, "interest_rate", 0.0))


def _loan_overdue_months(loan: object) -> int:
    if hasattr(loan, "overdue_months") and getattr(loan, "overdue_months") is not None:
        return max(int(getattr(loan, "overdue_months")), 0)

    due_date = getattr(loan, "due_date", None)
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    if isinstance(due_date, date):
        return _month_delta(date.today(), due_date)
    return 0


def _loan_emi(loan: object) -> float:
    if hasattr(loan, "emi") and getattr(loan, "emi") is not None:
        return _safe_float(getattr(loan, "emi"))

    balance = _loan_outstanding_amount(loan)
    interest_rate = _loan_interest_rate(loan)
    due_date = getattr(loan, "due_date", None)
    if isinstance(due_date, datetime):
        due_date = due_date.date()
    months_left = 12
    if isinstance(due_date, date):
        months_left = max(1, _month_delta(due_date, date.today()) or 1)

    monthly_rate = (interest_rate / 100.0) / 12.0
    if monthly_rate > 0:
        factor = (1 + monthly_rate) ** months_left
        denominator = factor - 1
        if denominator != 0:
            return round(balance * monthly_rate * factor / denominator, 2)

    return round(balance / months_left, 2) if months_left > 0 else round(balance, 2)


def calculate_financial_health(user, loans=None, existing_debts=None, outstanding_total: float = 0.0):
    """Calculate financial health metrics.

    Supports two call styles:
    - calculate_financial_health(user, loans) -> detailed report dict
    - calculate_financial_health(monthly_income, monthly_expenses, existing_debts, outstanding_total) -> legacy tuple
    """
    if loans is not None and not isinstance(loans, (int, float)):
        loan_list = list(loans)
        total_emi = sum(_loan_emi(loan) for loan in loan_list)
        total_outstanding = sum(_loan_outstanding_amount(loan) for loan in loan_list)
        monthly_income = _safe_float(getattr(user, "monthly_income", 0.0))
        monthly_expenses = _safe_float(getattr(user, "monthly_expenses", 0.0))
        surplus = monthly_income - monthly_expenses - total_emi

        if monthly_income > 0:
            emi_ratio = (total_emi / monthly_income) * 100
            debt_to_income = (total_outstanding / monthly_income) * 100
        else:
            emi_ratio = 0.0
            debt_to_income = 0.0

        if emi_ratio > 50:
            stress_level = "High"
        elif emi_ratio >= 30:
            stress_level = "Medium"
        else:
            stress_level = "Low"

        return {
            "total_emi": round(total_emi, 2),
            "total_outstanding": round(total_outstanding, 2),
            "surplus": round(surplus, 2),
            "emi_ratio_percent": round(emi_ratio, 2),
            "debt_to_income_percent": round(debt_to_income, 2),
            "stress_level": stress_level,
            "total_loans": len(loan_list),
        }

    monthly_income = _safe_float(user)
    monthly_expenses = _safe_float(loans)
    debts = _safe_float(existing_debts)
    outstanding = _safe_float(outstanding_total)

    if monthly_income <= 0:
        return 0.0, "Needs Attention", "No income data available."

    cash_flow = monthly_income - monthly_expenses - debts - outstanding * 0.1
    base_score = (cash_flow / monthly_income) * 100
    score = max(0.0, min(100.0, round(50.0 + base_score, 2)))

    if score >= 75:
        status = "Good"
    elif score >= 50:
        status = "Fair"
    else:
        status = "Needs Attention"

    message = f"Financial health assessed as {status.lower()} with score {score:.2f}."
    return score, status, message


def calculate_loan_priority(loans, emi_ratio: float = 0):
    priority_list = []

    for loan in loans:
        is_overdue = _loan_overdue_months(loan) > 0
        high_interest = _loan_interest_rate(loan) > 12
        high_emi_ratio = emi_ratio > 50

        if is_overdue or high_interest or high_emi_ratio:
            priority = "High"
        elif _loan_interest_rate(loan) > 8 or _loan_overdue_months(loan) > 0:
            priority = "Medium"
        else:
            priority = "Low"

        priority_list.append(
            {
                "loan_id": _loan_id(loan),
                "lender_name": _loan_lender_name(loan),
                "outstanding_amount": round(_loan_outstanding_amount(loan), 2),
                "interest_rate": round(_loan_interest_rate(loan), 2),
                "overdue_months": _loan_overdue_months(loan),
                "emi": round(_loan_emi(loan), 2),
                "priority": priority,
            }
        )

    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    priority_list.sort(key=lambda item: priority_order[item["priority"]])
    return priority_list


def calculate_settlement_recommendations(user, loans, financial_profile=None):
    monthly_income = _safe_float(getattr(financial_profile, "monthly_income", getattr(user, "monthly_income", 0.0)))
    monthly_expenses = _safe_float(getattr(financial_profile, "monthly_expenses", getattr(user, "monthly_expenses", 0.0)))
    existing_debts = _safe_float(getattr(financial_profile, "existing_debts", getattr(user, "existing_debts", 0.0)))

    loan_list = list(loans)
    total_emi = sum(_loan_emi(loan) for loan in loan_list)
    total_outstanding = sum(_loan_outstanding_amount(loan) for loan in loan_list)
    surplus = monthly_income - monthly_expenses - total_emi

    if monthly_income > 0:
        emi_ratio = (total_emi / monthly_income) * 100
        debt_to_income = (total_outstanding / monthly_income) * 100
    else:
        emi_ratio = 0.0
        debt_to_income = 0.0

    settlement_results = []

    for loan in loan_list:
        overdue_months = _loan_overdue_months(loan)
        settlement = 50.0
        risk_score = 0

        if overdue_months > 0:
            settlement += 5
            risk_score += 20

        if emi_ratio > 50:
            settlement += 5
            risk_score += 15

        if _loan_interest_rate(loan) > 12:
            settlement += 5
            risk_score += 10

        if debt_to_income > 80:
            settlement += 5
            risk_score += 15

        settlement = max(40.0, min(75.0, settlement))

        if risk_score >= 40:
            risk_category = "High"
        elif risk_score >= 20:
            risk_category = "Medium"
        else:
            risk_category = "Low"

        settlement_results.append(
            {
                "loan_id": _loan_id(loan),
                "lender_name": _loan_lender_name(loan),
                "outstanding_amount": round(_loan_outstanding_amount(loan), 2),
                "interest_rate": round(_loan_interest_rate(loan), 2),
                "emi": round(_loan_emi(loan), 2),
                "overdue_months": overdue_months,
                "suggested_settlement_percentage": round(settlement, 2),
                "recommended_settlement_amount": round(_loan_outstanding_amount(loan) * (settlement / 100.0), 2),
                "risk_score": risk_score,
                "risk_category": risk_category,
            }
        )

    risk_order = {"High": 0, "Medium": 1, "Low": 2}
    settlement_results.sort(key=lambda item: (risk_order[item["risk_category"]], -item["risk_score"]))

    return {
        "total_emi": round(total_emi, 2),
        "total_outstanding": round(total_outstanding, 2),
        "surplus": round(surplus, 2),
        "emi_ratio_percent": round(emi_ratio, 2),
        "debt_to_income_percent": round(debt_to_income, 2),
        "settlement_results": settlement_results,
    }


def simulate_debt_timeline(user, loans, extra_payment: float = 0):
    loan_data = [
        {
            "loan_id": _loan_id(loan),
            "balance": _loan_outstanding_amount(loan),
            "interest_rate": _loan_interest_rate(loan),
            "emi": _loan_emi(loan),
        }
        for loan in loans
    ]

    months = 0
    max_months = 240
    timeline = []

    while any(loan["balance"] > 0 for loan in loan_data) and months < max_months:
        months += 1
        total_balance = 0.0
        loan_data.sort(key=lambda item: item["balance"], reverse=True)

        for loan in loan_data:
            if loan["balance"] <= 0:
                continue

            monthly_interest = (loan["interest_rate"] / 100.0) / 12.0
            loan["balance"] += loan["balance"] * monthly_interest

            payment = loan["emi"]
            if extra_payment > 0 and loan == loan_data[0]:
                payment += extra_payment

            loan["balance"] -= payment
            if loan["balance"] < 0:
                loan["balance"] = 0.0

            total_balance += loan["balance"]

        timeline.append(
            {
                "month": months,
                "remaining_balance": round(total_balance, 2),
            }
        )

    return {
        "months_to_debt_free": months,
        "final_remaining_balance": round(total_balance, 2),
        "timeline_preview": timeline[:12],
    }


def build_settlement_prediction(
    health_score: float,
    loan_amount: float,
    outstanding_amount: float,
) -> tuple[str, float, str]:
    pressure = outstanding_amount / max(loan_amount, 1.0)

    if health_score >= 75 and pressure <= 0.5:
        prediction = "High settlement potential"
        recommended_amount = outstanding_amount * 0.45
        priority_level = "Low"
    elif health_score >= 50:
        prediction = "Moderate settlement potential"
        recommended_amount = outstanding_amount * 0.65
        priority_level = "Medium"
    else:
        prediction = "Low settlement potential"
        recommended_amount = outstanding_amount * 0.8
        priority_level = "High"

    return prediction, round(recommended_amount, 2), priority_level


def build_negotiation_strategy(
    user_name: str,
    loan_type: str,
    health_status: str,
    recommended_amount: float,
) -> str:
    return (
        f"Approach {loan_type.lower()} negotiation with a {health_status.lower()}-based plan for {user_name}. "
        f"Start near {recommended_amount:.2f}, request flexibility, and present a repayment timeline."
    )


def build_negotiation_email(
    user_name: str,
    loan_type: str,
    recommended_amount: float,
    strategy: str,
) -> tuple[str, str]:
    subject = f"Settlement request for {loan_type}"
    body = (
        f"Dear lender,\n\n"
        f"I am writing to request a settlement discussion for my {loan_type}.\n"
        f"Suggested settlement amount: {recommended_amount:.2f}.\n\n"
        f"Strategy: {strategy}\n\n"
        f"Regards,\n{user_name}"
    )
    return subject, body


def build_debt_timeline(total_outstanding: float, monthly_cash_flow: float, months: int = 6) -> list[dict[str, float | int]]:
    timeline: list[dict[str, float | int]] = []
    remaining = total_outstanding
    monthly_payment = max(monthly_cash_flow * 0.5, 0.0)

    for month in range(1, months + 1):
        remaining = max(0.0, round(remaining - monthly_payment, 2))
        timeline.append({"month": month, "projected_remaining": remaining})

    return timeline


def due_date_to_text(due_date: date) -> str:
    return due_date.strftime("%Y-%m-%d")