# NeoBank API — FastAPI + SQLite Backend

Full REST backend for the NeoBank QA Portfolio project.  
Deploy free on **Render.com** in ~3 minutes.

---

## 🚀 Deploy to Render (Free)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "NeoBank API"
git remote add origin https://github.com/YOUR_USERNAME/neobank-api.git
git push -u origin main
```

### Step 2 — Deploy on Render
1. Go to [render.com](https://render.com) → Sign up free
2. **New +** → **Web Service** → connect your GitHub repo
3. Set these fields:

| Field | Value |
|-------|-------|
| Environment | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

4. Add environment variables:
   - `SECRET_KEY` → click "Generate" for a random value
   - `DB_PATH` → `/var/data/neobank.db`

5. **Add a Disk** (for persistent SQLite):
   - Name: `neobank-db`
   - Mount Path: `/var/data`
   - Size: 1 GB (free tier)

6. Click **Deploy** — your API will be live at:
   `https://neobank-api.onrender.com`

---

## 🔑 Demo Credentials
```
Email:    demo@neobank.com
Password: demo1234
```

---

## 📋 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login → returns JWT token |
| POST | `/api/auth/register` | Register new user |

### Account
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/account/profile` | Get user profile |
| PUT | `/api/account/profile` | Update profile fields |
| GET | `/api/account/balance` | Get current balance |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List transactions (filterable) |
| GET | `/api/transactions/{id}` | Get single transaction |
| POST | `/api/transactions/transfer` | Make a transfer |

**Query params for GET /api/transactions:**
- `type` — `credit` or `debit`
- `category` — e.g. `Salary`, `Food & Dining`
- `status` — `completed`, `pending`
- `search` — text search on description/note
- `limit` / `offset` — pagination

### Loans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/loans` | List all loans |
| POST | `/api/loans/apply` | Apply for a loan |

### Fraud
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/fraud/check` | Run fraud risk check |

### Docs
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **Health:** `/health`

---

## 🔐 Authentication

All endpoints except login/register require a Bearer token:

```
Authorization: Bearer <token_from_login>
```

---

## 📬 Postman Collection

Import this JSON into Postman — update `base_url` to your Render URL.

```json
{
  "info": { "name": "NeoBank API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" },
  "variable": [
    { "key": "base_url", "value": "https://neobank-api.onrender.com" },
    { "key": "token", "value": "" }
  ],
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login (valid)",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 200', () => pm.response.to.have.status(200));",
            "const d = pm.response.json();",
            "pm.collectionVariables.set('token', d.access_token);",
            "pm.test('Has token', () => pm.expect(d.access_token).to.be.a('string'));"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/auth/login",
            "header": [{ "key": "Content-Type", "value": "application/json" }],
            "body": { "mode": "raw", "raw": "{\"email\":\"demo@neobank.com\",\"password\":\"demo1234\"}" }
          }
        },
        {
          "name": "Login (invalid password)",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 401', () => pm.response.to.have.status(401));"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/auth/login",
            "header": [{ "key": "Content-Type", "value": "application/json" }],
            "body": { "mode": "raw", "raw": "{\"email\":\"demo@neobank.com\",\"password\":\"wrong\"}" }
          }
        },
        {
          "name": "Register",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/auth/register",
            "header": [{ "key": "Content-Type", "value": "application/json" }],
            "body": { "mode": "raw", "raw": "{\"first_name\":\"Jane\",\"last_name\":\"Tester\",\"email\":\"jane@test.com\",\"password\":\"test1234\"}" }
          }
        }
      ]
    },
    {
      "name": "Account",
      "item": [
        {
          "name": "Get Balance",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 200', () => pm.response.to.have.status(200));",
            "pm.test('Has balance', () => pm.expect(pm.response.json().balance).to.be.a('number'));"
          ]}}],
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/account/balance",
            "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
          }
        },
        {
          "name": "Get Profile",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/account/profile",
            "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
          }
        }
      ]
    },
    {
      "name": "Transactions",
      "item": [
        {
          "name": "List All",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/transactions",
            "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
          }
        },
        {
          "name": "Filter Debit",
          "request": {
            "method": "GET",
            "url": { "raw": "{{base_url}}/api/transactions?type=debit", "query": [{ "key": "type", "value": "debit" }] },
            "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
          }
        },
        {
          "name": "Transfer (happy path)",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 201', () => pm.response.to.have.status(201));",
            "pm.test('Has tx id', () => pm.expect(pm.response.json().transaction_id).to.match(/^TX/));"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/transactions/transfer",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}" },
              { "key": "Content-Type", "value": "application/json" }
            ],
            "body": { "mode": "raw", "raw": "{\"recipient\":\"Alice Johnson\",\"amount\":100,\"note\":\"Test\"}" }
          }
        },
        {
          "name": "Transfer (over limit $10001)",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 422', () => pm.response.to.have.status(422));"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/transactions/transfer",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}" },
              { "key": "Content-Type", "value": "application/json" }
            ],
            "body": { "mode": "raw", "raw": "{\"recipient\":\"Alice Johnson\",\"amount\":10001}" }
          }
        },
        {
          "name": "Transfer (empty recipient)",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 422 or 400', () => pm.expect(pm.response.code).to.be.oneOf([400,422]));"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/transactions/transfer",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}" },
              { "key": "Content-Type", "value": "application/json" }
            ],
            "body": { "mode": "raw", "raw": "{\"recipient\":\"\",\"amount\":50}" }
          }
        }
      ]
    },
    {
      "name": "Fraud",
      "item": [
        {
          "name": "Low Risk",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('Status 200', () => pm.response.to.have.status(200));",
            "pm.test('LOW risk', () => pm.expect(pm.response.json().risk_level).to.eql('LOW'));"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/fraud/check",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}" },
              { "key": "Content-Type", "value": "application/json" }
            ],
            "body": { "mode": "raw", "raw": "{\"amount\":50,\"recipient\":\"Alice Johnson\"}" }
          }
        },
        {
          "name": "High Risk (large + unknown)",
          "event": [{ "listen": "test", "script": { "exec": [
            "pm.test('HIGH risk', () => pm.expect(pm.response.json().risk_level).to.eql('HIGH'));",
            "pm.test('Is flagged', () => pm.expect(pm.response.json().flagged).to.be.true);"
          ]}}],
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/fraud/check",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}" },
              { "key": "Content-Type", "value": "application/json" }
            ],
            "body": { "mode": "raw", "raw": "{\"amount\":6000,\"recipient\":\"Unknown Person\"}" }
          }
        }
      ]
    },
    {
      "name": "Loans",
      "item": [
        {
          "name": "List Loans",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/loans",
            "header": [{ "key": "Authorization", "value": "Bearer {{token}}" }]
          }
        },
        {
          "name": "Apply for Loan",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/loans/apply",
            "header": [
              { "key": "Authorization", "value": "Bearer {{token}}" },
              { "key": "Content-Type", "value": "application/json" }
            ],
            "body": { "mode": "raw", "raw": "{\"type\":\"Personal Loan\",\"amount\":5000,\"term_months\":24}" }
          }
        }
      ]
    }
  ]
}
```

---

## 🧪 QA Test Scenarios

### Boundary Value Tests
| Field | Test Value | Expected |
|-------|-----------|---------|
| Transfer | $0.01 | ✅ Valid |
| Transfer | $10,000 | ✅ Valid |
| Transfer | $10,000.01 | ❌ 422 |
| Transfer | $0 | ❌ 422 |
| Password | 7 chars | ❌ 422 |
| Password | 8 chars | ✅ Valid |
| Loan | $999 | ❌ 422 |
| Loan | $1,000 | ✅ Valid |

### Fraud Risk Logic
| Amount | Recipient | Expected Risk |
|--------|-----------|--------------|
| $50 | Alice Johnson | LOW |
| $2,500 | Alice Johnson | MEDIUM |
| $50 | Unknown Person | MEDIUM |
| $6,000 | Unknown Person | HIGH |

### SQL Validation (run against neobank.db)
```sql
-- Balance never goes negative
SELECT id, balance FROM users WHERE balance < 0;

-- Transfer amounts match debit transactions
SELECT SUM(amount) FROM transactions WHERE type='debit' AND category='Transfer';

-- Loan disbursement reflects in balance history
SELECT u.balance, l.amount FROM users u JOIN loans l ON u.id = l.user_id;

-- Transaction count matches filter
SELECT COUNT(*) FROM transactions WHERE type='debit';
```

---

## 🗂️ File Structure
```
neobank-backend/
├── main.py          ← All API routes (FastAPI)
├── database.py      ← SQLite setup + seed data
├── schemas.py       ← Request/response models (Pydantic)
├── auth.py          ← JWT + password hashing
├── requirements.txt ← Python dependencies
├── render.yaml      ← One-click Render deploy config
└── README.md        ← This file
```
