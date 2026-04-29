import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "neobank.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            account_type    TEXT DEFAULT 'checking',
            account_number  TEXT NOT NULL,
            balance         REAL DEFAULT 0.0,
            credit_score    INTEGER DEFAULT 720,
            member_since    TEXT NOT NULL,
            phone           TEXT DEFAULT '',
            address         TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT NOT NULL,
            category    TEXT DEFAULT 'Other',
            type        TEXT CHECK(type IN ('credit','debit')) NOT NULL,
            amount      REAL NOT NULL,
            status      TEXT DEFAULT 'completed',
            note        TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS loans (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            type            TEXT NOT NULL,
            amount          REAL NOT NULL,
            remaining       REAL NOT NULL,
            rate            REAL NOT NULL,
            monthly_payment REAL NOT NULL,
            status          TEXT DEFAULT 'active',
            applied_on      TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS fraud_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            recipient   TEXT NOT NULL,
            risk_level  TEXT NOT NULL,
            reason      TEXT NOT NULL,
            checked_at  TEXT NOT NULL
        );
    """)

    # Seed demo user
    existing = c.execute("SELECT id FROM users WHERE email = 'demo@neobank.com'").fetchone()
    if not existing:
        from passlib.context import CryptContext
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_ctx.hash("demo1234")

        c.execute("""
            INSERT INTO users (id, first_name, last_name, email, password,
                               account_type, account_number, balance,
                               credit_score, member_since, phone, address)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, ("USR001","John","Doe","demo@neobank.com", hashed,
              "checking","4821 7734 9902 4821", 24850.75,
              742, "2023-01-15", "+1 (555) 234-5678", "123 Main St, New York, NY"))

        txns = [
            ("TX001","USR001","2024-04-28","Salary Deposit","Salary","credit",5500,"completed","Monthly salary"),
            ("TX002","USR001","2024-04-25","Netflix Subscription","Entertainment","debit",15.99,"completed",""),
            ("TX003","USR001","2024-04-22","Grocery Store","Food & Dining","debit",124.50,"completed","Whole Foods"),
            ("TX004","USR001","2024-04-20","Freelance Payment","Income","credit",850,"completed",""),
            ("TX005","USR001","2024-04-18","Electric Bill","Bills & Utilities","debit",89.00,"completed",""),
            ("TX006","USR001","2024-04-15","Amazon Purchase","Shopping","debit",67.43,"completed",""),
            ("TX007","USR001","2024-04-10","ATM Withdrawal","Cash","debit",200,"completed",""),
            ("TX008","USR001","2024-04-05","Restaurant","Food & Dining","debit",45.20,"completed",""),
            ("TX009","USR001","2024-03-28","Salary Deposit","Salary","credit",5500,"completed","Monthly salary"),
            ("TX010","USR001","2024-03-15","Gym Membership","Health","debit",49.99,"completed",""),
        ]
        c.executemany("""
            INSERT INTO transactions (id,user_id,date,description,category,type,amount,status,note)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, txns)

        c.execute("""
            INSERT INTO loans (id,user_id,type,amount,remaining,rate,monthly_payment,status,applied_on)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, ("LN001","USR001","Personal Loan",15000,8750,7.5,465.50,"active","2023-06-10"))

    conn.commit()
    conn.close()
