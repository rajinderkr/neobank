from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uuid, os
from datetime import datetime

from database import get_connection, init_db
from schemas import (
    LoginRequest, RegisterRequest, TokenResponse,
    ProfileUpdate, UserProfile,
    Transaction, TransactionList, TransferRequest, TransferResponse,
    Loan, LoanApplication,
    FraudCheckRequest, FraudCheckResponse,
)
from auth import hash_password, verify_password, create_access_token, get_current_user

# ── App setup ─────────────────────────────────────────
app = FastAPI(
    title="NeoBank API",
    description="Full-featured digital banking API — built for QA practice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # lock down to your Netlify URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# ── Serve Frontend ────────────────────────────────────
@app.get("/", include_in_schema=False)
def serve_frontend():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"status": "ok", "message": "NeoBank API — place index.html next to main.py"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ══════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════
@app.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(body: LoginRequest):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (body.email.lower().strip(),)
    ).fetchone()
    conn.close()

    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials. Try demo@neobank.com / demo1234")

    token = create_access_token({"sub": user["id"]})
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        email=user["email"],
    )

@app.post("/api/auth/register", response_model=TokenResponse, tags=["Auth"], status_code=201)
def register(body: RegisterRequest):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (body.email.lower().strip(),)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Email already registered.")

    user_id = "USR" + str(uuid.uuid4())[:8].upper()
    account_number = " ".join([
        str(uuid.uuid4().int)[:4],
        str(uuid.uuid4().int)[:4],
        str(uuid.uuid4().int)[:4],
        str(uuid.uuid4().int)[:4],
    ])
    hashed = hash_password(body.password)
    now = datetime.utcnow().strftime("%Y-%m-%d")

    conn.execute("""
        INSERT INTO users (id, first_name, last_name, email, password,
                           account_type, account_number, balance,
                           credit_score, member_since, phone, address)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (user_id, body.first_name, body.last_name,
          body.email.lower().strip(), hashed,
          body.account_type or "checking", account_number,
          1000.00, 700, now, "", ""))
    conn.commit()
    conn.close()

    token = create_access_token({"sub": user_id})
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email.lower().strip(),
    )

# ══════════════════════════════════════════════════════
# ACCOUNT
# ══════════════════════════════════════════════════════
@app.get("/api/account/profile", response_model=UserProfile, tags=["Account"])
def get_profile(user_id: str = Depends(get_current_user)):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserProfile(**dict(user))

@app.put("/api/account/profile", response_model=UserProfile, tags=["Account"])
def update_profile(body: ProfileUpdate, user_id: str = Depends(get_current_user)):
    conn = get_connection()
    updates, values = [], []
    for field, value in body.model_dump(exclude_none=True).items():
        updates.append(f"{field} = ?")
        values.append(value)
    if updates:
        values.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return UserProfile(**dict(user))

@app.get("/api/account/balance", tags=["Account"])
def get_balance(user_id: str = Depends(get_current_user)):
    conn = get_connection()
    row = conn.execute("SELECT balance, account_number FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return {"balance": row["balance"], "account_number": row["account_number"]}

# ══════════════════════════════════════════════════════
# TRANSACTIONS
# ══════════════════════════════════════════════════════
@app.get("/api/transactions", response_model=TransactionList, tags=["Transactions"])
def list_transactions(
    type: Optional[str] = Query(None, description="credit | debit"),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    user_id: str = Depends(get_current_user),
):
    conn = get_connection()
    sql = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if type:
        sql += " AND type = ?"
        params.append(type)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if search:
        sql += " AND (description LIKE ? OR note LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    total = conn.execute(
        sql.replace("SELECT *", "SELECT COUNT(*)"), params
    ).fetchone()[0]

    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return TransactionList(
        transactions=[Transaction(**dict(r)) for r in rows],
        total=total,
    )

@app.get("/api/transactions/{tx_id}", response_model=Transaction, tags=["Transactions"])
def get_transaction(tx_id: str, user_id: str = Depends(get_current_user)):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return Transaction(**dict(row))

@app.post("/api/transactions/transfer", response_model=TransferResponse, tags=["Transactions"], status_code=201)
def transfer(body: TransferRequest, user_id: str = Depends(get_current_user)):
    if not body.recipient.strip():
        raise HTTPException(status_code=422, detail="Enter recipient name.")

    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    if user["balance"] < body.amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient funds.")

    new_balance = round(user["balance"] - body.amount, 2)
    tx_id = "TX" + str(uuid.uuid4())[:8].upper()
    now = datetime.utcnow().strftime("%Y-%m-%d")

    conn.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    conn.execute("""
        INSERT INTO transactions (id, user_id, date, description, category, type, amount, status, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, user_id, now, f"Transfer to {body.recipient}",
          "Transfer", "debit", body.amount, "completed", body.note or ""))
    conn.commit()
    conn.close()

    return TransferResponse(
        message="Transfer successful.",
        transaction_id=tx_id,
        new_balance=new_balance,
    )

# ══════════════════════════════════════════════════════
# LOANS
# ══════════════════════════════════════════════════════
@app.get("/api/loans", tags=["Loans"])
def list_loans(user_id: str = Depends(get_current_user)):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM loans WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return {"loans": [dict(r) for r in rows]}

@app.post("/api/loans/apply", tags=["Loans"], status_code=201)
def apply_loan(body: LoanApplication, user_id: str = Depends(get_current_user)):
    conn = get_connection()
    user = conn.execute("SELECT credit_score, balance FROM users WHERE id = ?", (user_id,)).fetchone()

    # Simple approval logic for QA testing
    if user["credit_score"] < 580:
        conn.close()
        raise HTTPException(status_code=400, detail="Loan denied: credit score too low.")

    rate = 5.0 if user["credit_score"] >= 750 else (7.5 if user["credit_score"] >= 670 else 12.0)
    monthly = round((body.amount * (rate / 100 / 12)) /
                    (1 - (1 + rate / 100 / 12) ** -body.term_months), 2)

    loan_id = "LN" + str(uuid.uuid4())[:8].upper()
    now = datetime.utcnow().strftime("%Y-%m-%d")

    conn.execute("""
        INSERT INTO loans (id, user_id, type, amount, remaining, rate, monthly_payment, status, applied_on)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (loan_id, user_id, body.type, body.amount, body.amount, rate, monthly, "active", now))

    # Disburse to balance
    conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (body.amount, user_id))
    conn.commit()

    new_balance = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()["balance"]
    conn.close()

    return {
        "message": "Loan approved!",
        "loan_id": loan_id,
        "amount": body.amount,
        "rate": rate,
        "monthly_payment": monthly,
        "new_balance": round(new_balance, 2),
    }

# ══════════════════════════════════════════════════════
# FRAUD CHECK
# ══════════════════════════════════════════════════════
KNOWN_RECIPIENTS = {"Alice Johnson", "Bob Smith", "Jane Doe", "David Wilson", "Emma Brown"}

@app.post("/api/fraud/check", response_model=FraudCheckResponse, tags=["Fraud"])
def fraud_check(body: FraudCheckRequest, user_id: str = Depends(get_current_user)):
    conn = get_connection()
    user = conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    risk_level = "LOW"
    reasons = []

    if body.amount > 5000:
        risk_level = "HIGH"
        reasons.append("Amount exceeds $5,000")
    elif body.amount > 2000:
        if risk_level != "HIGH":
            risk_level = "MEDIUM"
        reasons.append("Amount exceeds $2,000")

    if body.recipient not in KNOWN_RECIPIENTS:
        if risk_level == "LOW":
            risk_level = "MEDIUM"
        reasons.append("Unknown recipient")

    if user and body.amount > user["balance"] * 0.8:
        if risk_level == "LOW":
            risk_level = "MEDIUM"
        reasons.append("Transfer exceeds 80% of balance")

    reason = "; ".join(reasons) if reasons else "No suspicious activity detected."

    # Log it
    conn = get_connection()
    conn.execute("""
        INSERT INTO fraud_logs (user_id, amount, recipient, risk_level, reason, checked_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, body.amount, body.recipient, risk_level, reason,
          datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    return FraudCheckResponse(
        risk_level=risk_level,
        reason=reason,
        flagged=risk_level != "LOW",
    )
