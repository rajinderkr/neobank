from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

# ── Auth ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    account_type: Optional[str] = "checking"

    @field_validator("password")
    @classmethod
    def min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    first_name: str
    last_name: str
    email: str

# ── Account ───────────────────────────────────────────
class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    account_type: str
    account_number: str
    balance: float
    credit_score: int
    member_since: str
    phone: str
    address: str

# ── Transactions ──────────────────────────────────────
class Transaction(BaseModel):
    id: str
    date: str
    description: str
    category: str
    type: str
    amount: float
    status: str
    note: str

class TransactionList(BaseModel):
    transactions: List[Transaction]
    total: int

class TransferRequest(BaseModel):
    recipient: str
    amount: float
    note: Optional[str] = ""

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Enter a valid amount.")
        if v > 10000:
            raise ValueError("Transfer limit is $10,000.")
        return v

class TransferResponse(BaseModel):
    message: str
    transaction_id: str
    new_balance: float

# ── Loans ─────────────────────────────────────────────
class Loan(BaseModel):
    id: str
    type: str
    amount: float
    remaining: float
    rate: float
    monthly_payment: float
    status: str
    applied_on: str

class LoanApplication(BaseModel):
    type: str
    amount: float
    term_months: int

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v < 1000:
            raise ValueError("Minimum loan amount is $1,000.")
        if v > 500000:
            raise ValueError("Maximum loan amount is $500,000.")
        return v

# ── Fraud ─────────────────────────────────────────────
class FraudCheckRequest(BaseModel):
    amount: float
    recipient: str
    note: Optional[str] = ""

class FraudCheckResponse(BaseModel):
    risk_level: str   # LOW | MEDIUM | HIGH
    reason: str
    flagged: bool
