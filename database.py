import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              TEXT PRIMARY KEY,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            password        TEXT NOT NULL,
            account_type    TEXT DEFAULT 'checking',
            account_number  TEXT NOT NULL,
            balance         NUMERIC DEFAULT 0.0,
            credit_score    INTEGER DEFAULT 720,
            member_since    TEXT NOT NULL,
            phone           TEXT DEFAULT '',
            address         TEXT DEFAULT ''
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT NOT NULL,
            category    TEXT DEFAULT 'Other',
            type        TEXT CHECK(type IN ('credit','debit')) NOT NULL,
            amount      NUMERIC NOT NULL,
            status      TEXT DEFAULT 'completed',
            note        TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            type            TEXT NOT NULL,
            amount          NUMERIC NOT NULL,
            remaining       NUMERIC NOT NULL,
            rate            NUMERIC NOT NULL,
            monthly_payment NUMERIC NOT NULL,
            status          TEXT DEFAULT 'active',
            applied_on      TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fraud_logs (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL,
            amount      NUMERIC NOT NULL,
            recipient   TEXT NOT NULL,
            risk_level  TEXT NOT NULL,
            reason      TEXT NOT NULL,
            checked_at  TEXT NOT NULL
        );
    """)

    # Seed demo user
    c.execute("SELECT id FROM users WHERE email = %s", ('demo@neobank.com',))
    existing = c.fetchone()

    if not existing:
        from passlib.context import CryptContext

        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_ctx.hash("demo1234")

        c.execute("""
            INSERT INTO users (
                id, first_name, last_name, email, password,
                account_type, account_number, balance,
                credit_score, member_since, phone, address
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            "USR001",
            "John",
            "Doe",
            "demo@neobank.com",
            hashed,
            "checking",
            "4821 7734 9902 4821",
            24850.75,
            742,
            "2023-01-15",
            "+1 (555) 234-5678",
            "123 Main St, New York, NY"
        ))

        txns = [
            ("TX001","USR001","2024-04-28","Salary Deposit","Salary","credit",5500,"completed","Monthly salary"),
            ("TX002","USR001","2024-04-25","Netflix Subscription","Entertainment","debit",15.99,"completed",""),
        ]

        c.executemany("""
            INSERT INTO transactions (
                id,user_id,date,description,category,
                type,amount,status,note
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, txns)

        c.execute("""
            INSERT INTO loans (
                id,user_id,type,amount,remaining,
                rate,monthly_payment,status,applied_on
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            "LN001",
            "USR001",
            "Personal Loan",
            15000,
            8750,
            7.5,
            465.50,
            "active",
            "2023-06-10"
        ))

    conn.commit()
    c.close()
    conn.close()