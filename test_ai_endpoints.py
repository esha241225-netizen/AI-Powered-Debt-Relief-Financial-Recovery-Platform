"""Quick smoke test for all /ai/* endpoints."""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"
UID = 3

BASE_PAYLOAD = {
    "user_id": UID,
    "financial_profile": {
        "monthly_income": 80000,
        "monthly_expenses": 35000,
        "existing_debts": 5000,
        "financial_health_score": 60,
    },
    "loans": [
        {
            "loan_type": "Personal Loan",
            "lender_name": "HDFC Bank",
            "loan_amount": 500000,
            "outstanding_amount": 320000,
            "interest_rate": 14.5,
            "due_date": "2026-06-30",
            "overdue_months": 2,
        },
        {
            "loan_type": "Credit Card",
            "lender_name": "ICICI Bank",
            "loan_amount": 150000,
            "outstanding_amount": 95000,
            "interest_rate": 36.0,
            "due_date": "2025-12-31",
            "overdue_months": 0,
        },
    ],
}


def post(endpoint, payload):
    req = urllib.request.Request(
        BASE + endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


def get(endpoint):
    r = urllib.request.urlopen(BASE + endpoint)
    return json.loads(r.read())


if __name__ == "__main__":
    # Health check
    h = get("/ai/health")
    print(f"[HEALTH]  status={h['status']} | gemini={h['gemini_configured']} | model={h['model']}")

    # Negotiation strategy
    r1 = post("/ai/negotiation-strategy", BASE_PAYLOAD)
    print(f"[STRATEGY] user_id={r1['user_id']} | history_id={r1['history_id']} | ai_enhanced={r1['ai_enhanced']} | stress={r1['financial_health']['stress_level']}")

    # Settlement analysis
    r2 = post("/ai/settlement-analysis", BASE_PAYLOAD)
    print(f"[SETTLEMENT] history_id={r2['history_id']} | loans_analysed={len(r2['settlement_results'])} | ai_analysis keys={list(r2['ai_analysis'].keys())}")

    # Loan advice
    r3 = post("/ai/loan-advice", BASE_PAYLOAD)
    print(f"[ADVICE] history_id={r3['history_id']} | advice keys={list(r3['advice'].keys())}")

    # Repayment plan
    rp_payload = dict(BASE_PAYLOAD)
    rp_payload["extra_monthly_payment"] = 5000
    r4 = post("/ai/repayment-plan", rp_payload)
    print(f"[REPAYMENT] history_id={r4['history_id']} | plan keys={list(r4['repayment_plan'].keys())} | est_months={r4['repayment_plan'].get('estimated_debt_free_months')}")

    # Negotiation email
    email_payload = {
        "user_id": UID,
        "financial_profile": BASE_PAYLOAD["financial_profile"],
        "loan": BASE_PAYLOAD["loans"][0],
    }
    r5 = post("/ai/negotiation-email", email_payload)
    print(f"[EMAIL] history_id={r5['history_id']} | ai_enhanced={r5['ai_enhanced']} | subject={r5['subject'][:60]}")

    print("\nAll AI endpoints passed!")
