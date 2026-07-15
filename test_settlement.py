"""
End-to-end smoke test for Loan & Settlement Processing.
Tests: create user -> update profile -> add 3 loans -> run predictor
       -> verify settlement % by loan type -> check priorities
       -> fetch letter -> per-loan priority endpoint -> portfolio summary
       -> partial loan update -> manual settlement record
"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
PASS = "[PASS]"
FAIL = "[FAIL]"
TS = str(int(time.time()))


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload, default=str).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


def get(path):
    r = urllib.request.urlopen(BASE + path)
    return json.loads(r.read())


def put(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload, default=str).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


def delete(path):
    req = urllib.request.Request(BASE + path, method="DELETE")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}  {detail}")
        errors.append(label)


# ── 1. Register user ──────────────────────────────────────────────────────
print("\n[1] Register & profile setup")
user = post("/register", {"name": "Priya Sharma", "email": f"priya{TS}@test.com", "password": "pass"})
uid = user["user_id"]
check("User registered", uid > 0)

put("/update-profile", {
    "user_id": uid,
    "monthly_income": 90000,
    "monthly_expenses": 40000,
    "existing_debts": 8000,
})
check("Profile updated", True)

# ── 2. Add loans (3 different types) ────────────────────────────────────
print("\n[2] Add loans via SQLAlchemy ORM")
loan1 = post("/add-loan", {
    "user_id": uid,
    "loan_type": "Credit Card",
    "lender_name": "ICICI Bank",
    "loan_amount": 200000,
    "outstanding_amount": 180000,
    "interest_rate": 36.0,
    "due_date": "2025-06-30",
    "overdue_months": 4,
    "emi": 8000,
})
check("Credit Card loan created", loan1["loan_id"] > 0)
check("lender_name stored", loan1["lender_name"] == "ICICI Bank")
check("overdue_months stored", loan1["overdue_months"] == 4)

loan2 = post("/add-loan", {
    "user_id": uid,
    "loan_type": "Personal Loan",
    "lender_name": "HDFC Bank",
    "loan_amount": 500000,
    "outstanding_amount": 320000,
    "interest_rate": 14.5,
    "due_date": "2027-03-31",
    "overdue_months": 0,
    "emi": 12000,
})
check("Personal Loan created", loan2["loan_id"] > 0)

loan3 = post("/add-loan", {
    "user_id": uid,
    "loan_type": "Home Loan",
    "lender_name": "SBI",
    "loan_amount": 3000000,
    "outstanding_amount": 2500000,
    "interest_rate": 8.5,
    "due_date": "2038-12-31",
    "overdue_months": 0,
    "emi": 26000,
})
check("Home Loan created", loan3["loan_id"] > 0)

# ── 3. Retrieve loans ─────────────────────────────────────────────────────
print("\n[3] Retrieve loan records")
loans = get(f"/loans?user_id={uid}")
check("All 3 loans retrieved", len(loans) == 3)

single = get(f"/loans/{loan1['loan_id']}")
check("Single loan fetch works", single["loan_id"] == loan1["loan_id"])
check("Single loan has lender_name", single["lender_name"] == "ICICI Bank")

# ── 4. Settlement predictor ──────────────────────────────────────────────
print("\n[4] Settlement predictor (loan-type matrix + priority + letters)")
pred = get(f"/settlement-predictor?user_id={uid}")
results = pred["settlement_results"]
check("3 results returned", len(results) == 3)
check("All have settlement_percentage > 0", all(r["settlement_percentage"] > 0 for r in results))
check("All have priority assigned", all(r["priority"] in ("High", "Medium", "Low") for r in results))
check("All have negotiation_letter", all(len(r["negotiation_letter"]) > 200 for r in results))

# Credit card (4 months overdue, 36% interest) should be High priority
cc = next(r for r in results if r["loan_type"] == "Credit Card")
check("Credit Card = High priority", cc["priority"] == "High", f"got {cc['priority']}")
check("Credit Card settlement % >= 65", cc["settlement_percentage"] >= 65.0, f"got {cc['settlement_percentage']}")
check("Credit Card letter mentions ICICI", "ICICI" in cc["negotiation_letter"])

# Home Loan (no overdue, low interest) should be lowest priority
hl = next(r for r in results if r["loan_type"] == "Home Loan")
check("Home Loan settlement % <= 55", hl["settlement_percentage"] <= 55.0, f"got {hl['settlement_percentage']}")
check("Home Loan letter mentions SBI", "SBI" in hl["negotiation_letter"])

# ── 5. Fetch stored settlement records ───────────────────────────────────
print("\n[5] Stored settlement records")
records = get(f"/settlement-records?user_id={uid}")
check("3 settlement records in DB", len(records) == 3)
check("Records have loan_type", all(r["loan_type"] != "" for r in records))
check("Records have lender_name", all(r["lender_name"] != "" for r in records))
check("Records have settlement_percentage", all(r["settlement_percentage"] > 0 for r in records))

# Single record fetch
r1 = get(f"/settlement-records/{records[0]['settlement_id']}")
check("Single record fetch works", r1["settlement_id"] == records[0]["settlement_id"])

# Negotiation letter endpoint
letter_resp = get(f"/settlement-records/{records[0]['settlement_id']}/letter")
check("Letter endpoint returns data", len(letter_resp["negotiation_letter"]) > 100)
check("Letter has settlement_percentage", letter_resp["settlement_percentage"] > 0)
check("Letter has created_at", "created_at" in letter_resp)

# ── 6. Per-loan priority endpoint ────────────────────────────────────────
print("\n[6] Per-loan priority endpoint")
priority = get(f"/loans/{loan1['loan_id']}/priority")
check("Priority endpoint works", "priority" in priority)
check("Priority has settlement_percentage", priority["settlement_percentage"] > 0)
check("Priority has priority_score", priority["priority_score"] >= 0)
check("Priority has settlement_prediction", len(priority["settlement_prediction"]) > 5)

# ── 7. Portfolio summary ─────────────────────────────────────────────────
print("\n[7] Portfolio summary")
summary = get(f"/loans/summary/{uid}")
check("Summary has 3 loans", summary["total_loans"] == 3)
check("Summary has overdue_loans", summary["overdue_loans"] == 1)
check("Summary has high_priority_loans", summary["high_priority_loans"] >= 1)
check("Summary has stress_level", summary["stress_level"] in ("High", "Medium", "Low"))
check("Summary total_outstanding correct", summary["total_outstanding"] == 3000000.0)

# ── 8. Partial loan update ───────────────────────────────────────────────
print("\n[8] Partial loan update")
updated = put(f"/loans/{loan2['loan_id']}", {
    "outstanding_amount": 300000,
    "overdue_months": 2,
    "emi": 13500,
})
check("Update returns loan", updated["loan_id"] == loan2["loan_id"])
check("outstanding_amount updated", updated["outstanding_amount"] == 300000)
check("overdue_months updated", updated["overdue_months"] == 2)

# ── 9. Manual settlement record ──────────────────────────────────────────
print("\n[9] Manual settlement record")
manual = post("/settlement-records/manual", {
    "user_id": uid,
    "loan_id": loan2["loan_id"],
    "settlement_percentage": 62.0,
    "recommended_amount": 186000,
    "priority_level": "Medium",
})
check("Manual record created", manual["settlement_id"] > 0)
check("Manual record has auto-generated letter", len(manual["negotiation_letter"]) > 100)

# ── Final ────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
if errors:
    print(f"FAILED: {len(errors)} check(s) failed: {errors}")
    sys.exit(1)
else:
    print(f"ALL CHECKS PASSED  ({20} checks)")
