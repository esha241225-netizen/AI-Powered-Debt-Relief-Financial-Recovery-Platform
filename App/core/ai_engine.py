"""
ai_engine.py
============
Dedicated Google Gemini AI engine for FinRelief AI.

Responsibilities
----------------
* Build rich, context-aware prompts from loan details and financial profile.
* Call the Google Gemini API (gemini-1.5-flash) and return raw text.
* Parse the raw text response into validated, structured Python dicts.
* Provide deterministic rule-based fallbacks when Gemini is unavailable.

All public helpers return plain Python dicts / strings so that FastAPI
routers can serialise them directly via Pydantic response models.
"""

from __future__ import annotations

import importlib
import json
import os
import re
from datetime import date
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# ---------------------------------------------------------------------------
# Low-level Gemini call
# ---------------------------------------------------------------------------


def _call_gemini(prompt: str) -> str | None:
    """Send *prompt* to Gemini and return the raw text response.

    Returns ``None`` when the API is unavailable or an error occurs so that
    callers can fall back to rule-based logic.
    """
    if not GOOGLE_API_KEY:
        return None

    try:
        genai = importlib.import_module("google.generativeai")
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[ai_engine] Gemini API error: {exc}")
        return None


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any] | None:
    """Try to extract the first JSON object from *text*."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    # Find first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def _financial_summary_block(financial_profile: dict[str, Any]) -> str:
    """Format financial profile fields into a readable prompt block."""
    return (
        f"  Monthly Income : ₹{financial_profile.get('monthly_income', 0):,.2f}\n"
        f"  Monthly Expenses: ₹{financial_profile.get('monthly_expenses', 0):,.2f}\n"
        f"  Existing Debts  : ₹{financial_profile.get('existing_debts', 0):,.2f}\n"
        f"  Health Score    : {financial_profile.get('financial_health_score', 0):.1f}/100"
    )


def _loans_block(loans: list[dict[str, Any]]) -> str:
    """Format a list of loan dicts into a numbered prompt block."""
    if not loans:
        return "  No loans provided."
    lines = []
    for i, loan in enumerate(loans, 1):
        lines.append(
            f"  Loan {i}: {loan.get('loan_type', 'Unknown')} | "
            f"Outstanding ₹{loan.get('outstanding_amount', 0):,.2f} | "
            f"Rate {loan.get('interest_rate', 0):.2f}% | "
            f"Due {loan.get('due_date', 'N/A')} | "
            f"Overdue {loan.get('overdue_months', 0)} month(s)"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public AI functions
# ---------------------------------------------------------------------------


def generate_negotiation_strategy(
    user_name: str,
    financial_profile: dict[str, Any],
    loans: list[dict[str, Any]],
    financial_health: dict[str, Any],
    settlement_data: dict[str, Any],
) -> str:
    """Generate a personalised debt-negotiation strategy.

    Tries Gemini first; falls back to a deterministic template.
    """
    prompt = f"""
You are an expert financial advisor helping {user_name} negotiate debt settlements.

FINANCIAL PROFILE:
{_financial_summary_block(financial_profile)}

LOANS:
{_loans_block(loans)}

FINANCIAL HEALTH METRICS:
  Stress Level        : {financial_health.get('stress_level', 'Unknown')}
  EMI-to-Income Ratio : {financial_health.get('emi_ratio_percent', 0):.1f}%
  Debt-to-Income Ratio: {financial_health.get('debt_to_income_percent', 0):.1f}%
  Monthly Surplus     : ₹{financial_health.get('surplus', 0):,.2f}

Provide a concise, practical negotiation strategy (3-5 paragraphs) that:
1. Prioritises the highest-risk loans first.
2. Suggests realistic settlement percentages (40-75% of outstanding).
3. Recommends a step-by-step negotiation approach with lenders.
4. Advises on protecting the borrower's credit score.
5. Proposes a manageable monthly repayment plan based on the surplus.

Write directly to {user_name}. Be empathetic but professional.
"""
    result = _call_gemini(prompt)
    if result:
        return result.strip()

    # --- Rule-based fallback ---
    stress = financial_health.get("stress_level", "Medium")
    surplus = financial_health.get("surplus", 0)
    total_outstanding = financial_health.get("total_outstanding", 0)
    emi_ratio = financial_health.get("emi_ratio_percent", 0)

    pct = 50 if stress == "Low" else (60 if stress == "Medium" else 70)
    settlement_amt = round(total_outstanding * pct / 100, 2)

    return (
        f"Dear {user_name},\n\n"
        f"Based on your current financial profile, your debt stress level is **{stress}** "
        f"with an EMI-to-income ratio of {emi_ratio:.1f}%. "
        f"Your monthly surplus of ₹{surplus:,.2f} provides some negotiation flexibility.\n\n"
        f"**Recommended Strategy:**\n"
        f"1. Target a lump-sum settlement of approximately {pct}% of outstanding balances "
        f"(₹{settlement_amt:,.2f} total).\n"
        f"2. Prioritise overdue loans first — lenders are more willing to negotiate on aged debt.\n"
        f"3. Contact each lender's collections department directly and present your hardship case "
        f"with documented income/expense statements.\n"
        f"4. Request waiver of penal interest and foreclosure charges as part of settlement.\n"
        f"5. Obtain a **No Objection Certificate (NOC)** after each settlement to protect your CIBIL score.\n\n"
        f"Allocate at least 30% of your monthly surplus (₹{surplus * 0.3:,.2f}) towards accelerated "
        f"debt repayment while negotiations are ongoing."
    )


def generate_settlement_analysis(
    user_name: str,
    financial_profile: dict[str, Any],
    loans: list[dict[str, Any]],
    settlement_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate an AI-enhanced settlement analysis with actionable recommendations.

    Returns a structured dict with keys:
      - ``summary`` (str)
      - ``priority_actions`` (list[str])
      - ``risk_assessment`` (str)
      - ``ai_enhanced`` (bool)
    """
    prompt = f"""
You are a debt settlement expert. Analyse the following settlement data for {user_name}
and respond with ONLY a valid JSON object — no markdown, no extra text.

FINANCIAL PROFILE:
{_financial_summary_block(financial_profile)}

SETTLEMENT ANALYSIS RESULTS:
{json.dumps(settlement_results, indent=2, default=str)}

Respond with this exact JSON structure:
{{
  "summary": "<2-3 sentence executive summary>",
  "priority_actions": [
    "<action 1>",
    "<action 2>",
    "<action 3>"
  ],
  "risk_assessment": "<1-2 sentence overall risk assessment>",
  "recommended_total_settlement": <number>,
  "estimated_savings": <number>
}}
"""
    raw = _call_gemini(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed:
            parsed["ai_enhanced"] = True
            return parsed

    # --- Rule-based fallback ---
    total_outstanding = sum(r.get("outstanding_amount", 0) for r in settlement_results)
    total_settlement = sum(r.get("recommended_settlement_amount", 0) for r in settlement_results)
    savings = total_outstanding - total_settlement
    high_risk = [r for r in settlement_results if r.get("risk_category") == "High"]

    actions = [
        f"Immediately contact lender for {r['lender_name']} — overdue {r.get('overdue_months', 0)} month(s)"
        for r in high_risk[:3]
    ]
    if not actions:
        actions = [
            "Consolidate high-interest loans for better negotiation leverage",
            "Build 3-month emergency fund before initiating settlements",
            "Request lender hardship programmes for interest rate reductions",
        ]

    return {
        "summary": (
            f"{user_name} has {len(settlement_results)} loan(s) with a total outstanding of "
            f"₹{total_outstanding:,.2f}. Settling at recommended percentages would cost "
            f"approximately ₹{total_settlement:,.2f}, saving ₹{savings:,.2f}."
        ),
        "priority_actions": actions,
        "risk_assessment": (
            f"{'High' if high_risk else 'Moderate'} overall risk — "
            f"{len(high_risk)} loan(s) require immediate attention."
        ),
        "recommended_total_settlement": round(total_settlement, 2),
        "estimated_savings": round(savings, 2),
        "ai_enhanced": False,
    }


def generate_loan_advice(
    user_name: str,
    financial_profile: dict[str, Any],
    loans: list[dict[str, Any]],
    financial_health: dict[str, Any],
) -> dict[str, Any]:
    """Generate per-loan AI advice and an overall financial action plan.

    Returns a structured dict with keys:
      - ``overall_advice`` (str)
      - ``loan_specific_advice`` (list[dict])
      - ``repayment_plan`` (str)
      - ``ai_enhanced`` (bool)
    """
    prompt = f"""
You are a certified financial planner. Provide personalised loan management advice for {user_name}.
Respond with ONLY a valid JSON object — no markdown, no extra text.

FINANCIAL PROFILE:
{_financial_summary_block(financial_profile)}

LOANS:
{json.dumps(loans, indent=2, default=str)}

HEALTH METRICS:
  Stress Level : {financial_health.get('stress_level', 'Medium')}
  Monthly Surplus: ₹{financial_health.get('surplus', 0):,.2f}

Respond with this exact JSON structure:
{{
  "overall_advice": "<3-4 sentence overall financial advice>",
  "loan_specific_advice": [
    {{
      "loan_type": "<type>",
      "advice": "<specific action for this loan>",
      "urgency": "High|Medium|Low"
    }}
  ],
  "repayment_plan": "<concrete monthly repayment strategy>",
  "quick_wins": ["<win 1>", "<win 2>", "<win 3>"]
}}
"""
    raw = _call_gemini(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed:
            parsed["ai_enhanced"] = True
            return parsed

    # --- Rule-based fallback ---
    stress = financial_health.get("stress_level", "Medium")
    surplus = financial_health.get("surplus", 0)

    loan_advice = []
    for loan in loans:
        overdue = loan.get("overdue_months", 0)
        rate = loan.get("interest_rate", 0)
        urgency = "High" if overdue > 0 or rate > 15 else ("Medium" if rate > 10 else "Low")
        advice = (
            f"Pay overdue EMIs immediately to stop penalty accumulation."
            if overdue > 0
            else f"Consider prepayment to reduce interest burden (rate: {rate:.1f}%)."
        )
        loan_advice.append({
            "loan_type": loan.get("loan_type", "Unknown"),
            "advice": advice,
            "urgency": urgency,
        })

    return {
        "overall_advice": (
            f"Your financial stress level is {stress}. "
            f"With a monthly surplus of ₹{surplus:,.2f}, you have capacity to accelerate debt repayment. "
            f"Focus on eliminating high-interest and overdue loans first. "
            f"Avoid taking on new debt until your EMI-to-income ratio falls below 30%."
        ),
        "loan_specific_advice": loan_advice,
        "repayment_plan": (
            f"Allocate ₹{max(surplus * 0.5, 0):,.2f}/month (50% of surplus) to debt reduction. "
            f"Use the avalanche method — pay minimums on all loans, then direct extra payments "
            f"to the highest-interest loan until cleared, then roll that payment to the next."
        ),
        "quick_wins": [
            "Set up auto-debit to never miss an EMI",
            "Call your top lender and request a 1-2% interest rate reduction",
            "Liquidate any idle savings earning less than your loan interest rates",
        ],
        "ai_enhanced": False,
    }


def generate_negotiation_email(
    user_name: str,
    loan_type: str,
    lender_name: str,
    outstanding_amount: float,
    recommended_settlement: float,
    financial_profile: dict[str, Any],
) -> dict[str, str]:
    """Generate a professional negotiation / hardship letter to a lender.

    Returns ``{"subject": ..., "body": ...}``.
    """
    prompt = f"""
Draft a professional debt settlement letter from {user_name} to {lender_name}
for a {loan_type} with outstanding balance of ₹{outstanding_amount:,.2f}.
The proposed settlement amount is ₹{recommended_settlement:,.2f}.

Monthly Income   : ₹{financial_profile.get('monthly_income', 0):,.2f}
Monthly Expenses : ₹{financial_profile.get('monthly_expenses', 0):,.2f}

The letter must:
- Be formal and respectful
- Clearly state the hardship situation
- Propose the settlement amount with justification
- Request a No Objection Certificate upon settlement
- Be under 300 words

Respond with ONLY a valid JSON object:
{{
  "subject": "<email subject line>",
  "body": "<full letter body with newlines as \\n>"
}}
"""
    raw = _call_gemini(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed and "subject" in parsed and "body" in parsed:
            return parsed

    # --- Rule-based fallback ---
    subject = f"Settlement Request for {loan_type} Account — {user_name}"
    body = (
        f"Dear {lender_name} Collections Team,\n\n"
        f"I am writing to formally request a one-time settlement for my {loan_type} account.\n\n"
        f"Due to unforeseen financial hardship, I am unable to service the full outstanding amount "
        f"of ₹{outstanding_amount:,.2f}. After reviewing my income and expenses, I am in a position "
        f"to offer a lump-sum settlement of ₹{recommended_settlement:,.2f} "
        f"({(recommended_settlement/max(outstanding_amount,1)*100):.0f}% of outstanding balance).\n\n"
        f"I believe this offer is fair and represents the maximum I can afford. Accepting this "
        f"settlement will allow you to recover a meaningful portion of the debt and avoid prolonged "
        f"collection efforts.\n\n"
        f"I kindly request:\n"
        f"1. Written confirmation of acceptance of this settlement offer.\n"
        f"2. Waiver of all penal interest and charges upon settlement.\n"
        f"3. Issuance of a No Objection Certificate (NOC) within 7 working days of payment.\n\n"
        f"Please contact me to discuss this proposal at your earliest convenience.\n\n"
        f"Sincerely,\n{user_name}"
    )
    return {"subject": subject, "body": body}


def generate_repayment_plan(
    user_name: str,
    financial_profile: dict[str, Any],
    loans: list[dict[str, Any]],
    financial_health: dict[str, Any],
    extra_monthly_payment: float = 0.0,
) -> dict[str, Any]:
    """Generate a month-by-month repayment plan using the avalanche strategy.

    Returns a structured dict with keys:
      - ``strategy_name`` (str)
      - ``monthly_allocation`` (float)
      - ``estimated_debt_free_months`` (int)
      - ``total_interest_saved`` (float)
      - ``steps`` (list[dict])
      - ``ai_enhanced`` (bool)
    """
    surplus = financial_health.get("surplus", 0)
    allocation = max(surplus * 0.5, 0) + extra_monthly_payment
    total_outstanding = financial_health.get("total_outstanding", sum(
        l.get("outstanding_amount", 0) for l in loans
    ))

    prompt = f"""
Create a practical debt repayment plan for {user_name} using the avalanche method.
Respond with ONLY a valid JSON object — no markdown.

Monthly allocation for extra debt repayment: ₹{allocation:,.2f}
Total outstanding debt: ₹{total_outstanding:,.2f}
Monthly surplus: ₹{surplus:,.2f}

Loans (sorted by interest rate descending):
{json.dumps(sorted(loans, key=lambda l: l.get('interest_rate', 0), reverse=True), indent=2, default=str)}

Respond with:
{{
  "strategy_name": "<name of strategy>",
  "monthly_allocation": {allocation},
  "estimated_debt_free_months": <integer>,
  "total_interest_saved": <number>,
  "steps": [
    {{"month_range": "<e.g. Months 1-6>", "action": "<what to do>", "target_loan": "<loan type>"}}
  ],
  "tips": ["<tip 1>", "<tip 2>"]
}}
"""
    raw = _call_gemini(prompt)
    if raw:
        parsed = _extract_json(raw)
        if parsed:
            parsed["ai_enhanced"] = True
            return parsed

    # --- Rule-based fallback ---
    monthly_payment = max(allocation, 1)
    months = int(total_outstanding / monthly_payment) if monthly_payment > 0 else 999
    interest_saved = round(total_outstanding * 0.15, 2)  # rough estimate

    sorted_loans = sorted(loans, key=lambda l: l.get("interest_rate", 0), reverse=True)
    steps = []
    if sorted_loans:
        steps.append({
            "month_range": "Months 1-6",
            "action": f"Direct extra ₹{allocation:,.2f}/month to highest-rate loan",
            "target_loan": sorted_loans[0].get("loan_type", "Unknown"),
        })
        if len(sorted_loans) > 1:
            steps.append({
                "month_range": "Months 7+",
                "action": "Roll entire payment to next highest-rate loan after first is cleared",
                "target_loan": sorted_loans[1].get("loan_type", "Unknown"),
            })

    return {
        "strategy_name": "Debt Avalanche (Highest Interest First)",
        "monthly_allocation": round(allocation, 2),
        "estimated_debt_free_months": months,
        "total_interest_saved": interest_saved,
        "steps": steps,
        "tips": [
            "Increase allocation by 10% whenever you receive a raise or bonus",
            "Avoid new credit until all high-interest loans are cleared",
        ],
        "ai_enhanced": False,
    }
