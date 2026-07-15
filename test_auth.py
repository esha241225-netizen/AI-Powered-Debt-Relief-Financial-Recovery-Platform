"""JWT Authentication + SQLite indexed query smoke test."""
import json, sys, time, urllib.request, urllib.error, sqlite3

BASE  = "http://127.0.0.1:8001"
TS    = str(int(time.time()))
EMAIL = f"jwt_{TS}@finrelief.com"
PASS  = "SecureP@ss1"
PASS2 = "NewP@ss9876"
errors = []

def post(path, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE+path, data=json.dumps(payload).encode(), headers=headers, method="POST")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def get(path, token=None):
    headers = {}
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE+path, headers=headers)
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def put(path, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE+path, data=json.dumps(payload).encode(), headers=headers, method="PUT")
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def expect_status(path, expected_code, token=None, method="GET"):
    try:
        headers = {}
        if token: headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(BASE+path, headers=headers, method=method)
        urllib.request.urlopen(req)
        return False
    except urllib.error.HTTPError as e:
        return e.code == expected_code

def check(label, cond, detail=""):
    tag = "[PASS]" if cond else "[FAIL]"
    print(f"  {tag} {label}" + (f"  | {detail}" if detail else ""))
    if not cond:
        errors.append(label)

# ── 1. Register ────────────────────────────────────────────────────────────
print("\n[1] Registration - bcrypt hash + immediate JWT")
reg = post("/auth/register", {"name": "JWT Tester", "email": EMAIL, "password": PASS})
check("Register returns access_token", "access_token" in reg)
check("Register token_type=bearer", reg.get("token_type") == "bearer")
check("Register expires_in_minutes=1440", reg.get("expires_in_minutes") == 1440)
check("Register returns user object", "user" in reg)
check("Password NOT in response", "password" not in reg["user"])
TOKEN = reg["access_token"]
UID   = reg["user"]["user_id"]

# ── 2. Duplicate email rejected ────────────────────────────────────────────
print("\n[2] Duplicate registration rejected")
try:
    post("/auth/register", {"name": "Dup", "email": EMAIL, "password": PASS})
    check("Duplicate rejected", False)
except urllib.error.HTTPError as e:
    check("Duplicate rejected with 400", e.code == 400)

# ── 3. Login ───────────────────────────────────────────────────────────────
print("\n[3] Login - indexed email lookup + JWT issuance")
login = post("/auth/login", {"email": EMAIL, "password": PASS})
check("Login returns access_token", "access_token" in login)
check("Login message correct", login["message"] == "Login successful")
TOKEN = login["access_token"]

# ── 4. Wrong credentials rejected ─────────────────────────────────────────
print("\n[4] Wrong credentials rejected")
try:
    post("/auth/login", {"email": EMAIL, "password": "wrongpass"})
    check("Wrong password rejected", False)
except urllib.error.HTTPError as e:
    check("Wrong password gives 401", e.code == 401)

# ── 5. Protected routes without token return 401 ──────────────────────────
print("\n[5] Unauthenticated access returns 401")
check("/auth/me without token = 401", expect_status("/auth/me", 401))
check("/dashboard-data without token = 401", expect_status("/dashboard-data", 401))
check("/loans without token = 401", expect_status("/loans", 401))
check("/settlement-predictor without token = 401", expect_status("/settlement-predictor", 401))
check("/financial-health without token = 401", expect_status("/financial-health", 401))

# ── 6. /auth/me ────────────────────────────────────────────────────────────
print("\n[6] /auth/me with valid token")
me = get("/auth/me", token=TOKEN)
check("/auth/me works", "user" in me)
check("/auth/me returns correct user_id", me["user"]["user_id"] == UID)
check("/auth/me has financial_profile key", "financial_profile" in me)

# ── 7. Protected routes work with token ───────────────────────────────────
print("\n[7] Protected routes accessible with valid JWT")
put("/update-profile", {"user_id": UID, "monthly_income": 80000,
    "monthly_expenses": 35000, "existing_debts": 5000}, token=TOKEN)
loans = get("/loans", token=TOKEN)
check("/loans accessible with token", isinstance(loans, list))
dashboard = get("/dashboard-data", token=TOKEN)
check("/dashboard-data accessible", "user" in dashboard)
check("Dashboard user_id matches token", dashboard["user"]["user_id"] == UID)

# ── 8. Token refresh ──────────────────────────────────────────────────────
print("\n[8] Token refresh")
refresh = post("/auth/refresh", {}, token=TOKEN)
check("Refresh returns new token", "access_token" in refresh)
NEW_TOKEN = refresh["access_token"]
check("Refreshed token is a valid JWT string", len(NEW_TOKEN) > 50)
# New token also works
me2 = get("/auth/me", token=NEW_TOKEN)
check("Refreshed token is valid", me2["user"]["user_id"] == UID)

# ── 9. Loan ownership enforcement ─────────────────────────────────────────
print("\n[9] Loan ownership - cross-user access blocked (403)")
other = post("/auth/register", {"name": "Other User", "email": f"other{TS}@test.com", "password": "other1234"})
OTHER_TOKEN = other["access_token"]
loan = post("/add-loan", {
    "user_id": UID, "loan_type": "Personal Loan", "lender_name": "HDFC",
    "loan_amount": 100000, "outstanding_amount": 80000, "interest_rate": 14.0,
    "due_date": "2027-01-01", "overdue_months": 0
}, token=TOKEN)
loan_id = loan["loan_id"]
try:
    get(f"/loans/{loan_id}", token=OTHER_TOKEN)
    check("Cross-user loan access blocked", False)
except urllib.error.HTTPError as e:
    check("Cross-user loan access gives 403", e.code == 403)

# ── 10. Change password ───────────────────────────────────────────────────
print("\n[10] Change password")
cpw = put("/auth/change-password", {"current_password": PASS, "new_password": PASS2}, token=TOKEN)
check("Change password returns new token", "access_token" in cpw)
try:
    post("/auth/login", {"email": EMAIL, "password": PASS})
    check("Old password rejected after change", False)
except urllib.error.HTTPError as e:
    check("Old password rejected after change", e.code == 401)
new_login = post("/auth/login", {"email": EMAIL, "password": PASS2})
check("New password accepted on login", "access_token" in new_login)

# ── 11. SQLite indexed queries ────────────────────────────────────────────
print("\n[11] SQLite - indexed per-session queries")
conn = sqlite3.connect("finrelief.db")
cur  = conn.cursor()
u_idx = [row[1] for row in cur.execute("PRAGMA index_list('users')").fetchall()]
l_idx = [row[1] for row in cur.execute("PRAGMA index_list('loans')").fetchall()]
s_idx = [row[1] for row in cur.execute("PRAGMA index_list('settlement_records')").fetchall()]
check("users.email index exists (fast login lookups)", any("email" in x for x in u_idx), str(u_idx))
check("loans.user_id index exists (per-session queries)", any("user_id" in x for x in l_idx), str(l_idx))
check("settlement_records.user_id index exists", any("user_id" in x for x in s_idx), str(s_idx))
conn.close()

# ── Final ─────────────────────────────────────────────────────────────────
print(f"\n{'='*62}")
if errors:
    print(f"FAILED: {len(errors)} check(s) -- {errors}")
    sys.exit(1)
else:
    total = 5+2+2+1+5+3+3+3+1+3+3
    print(f"ALL AUTH CHECKS PASSED ({total} checks)")
