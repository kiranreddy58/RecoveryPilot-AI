# RecoveryPilot AI
> **Autonomous Revenue Recovery Control Tower for Modern Merchants**  
> *Built for Razorpay Buildathon — Track 03: AI Revenue Recovery*

---

## What is RecoveryPilot AI?

When an online transaction fails, merchants usually have two bad options:
1. **Dumb automation:** Blast the customer with blind retries and spam messages until the payment gateway bans them or the customer gets angry.
2. **Naive AI chatbots:** Give a non-deterministic LLM direct access to refund or discount tools and risk hallucinations giving away 50% discounts.

**RecoveryPilot AI** takes a different approach. It acts as an autonomous revenue recovery control tower that pairs **AI decision intelligence** with a **strict, deterministic Policy Guardian**:

- **AI proposes** candidate recovery actions based on failure telemetry.
- **Policy Guardian validates** every action against hard business rules before anything executes.
- **Closed-loop webhooks** listen for customer payments and reconcile cases automatically.
- **Cryptographic SHA-256 micro-blocks** log every lifecycle state change for tamper-evident auditing.

```
Incoming Failure Event
       │
       ▼
1. Risk Detection ────────► Classify failure category (Payment, Subscription, Checkout drop-off)
       │
       ▼
2. AI Diagnosis ──────────► Live LLM diagnoses root cause with confidence score
       │
       ▼
3. Strategy Evaluation ───► Compute Expected Net Recovery across candidate actions
       │
       ▼
4. Policy Guardian ───────► Deterministic safety gate: retries <= 2, frequency >= 24h, discount <= 10%
       │
  ┌────┴──────────────────────────┐
  ▼                               ▼
APPROVED                      ESCALATED / BLOCKED
  │                               │
  ▼                               ▼
5. Bounded Execution          Human Approval Queue / Halt
  │
  ▼
6. Closed-Loop Webhook ───► Ingest 'payment_link.paid' -> Mark RECOVERED & log SHA-256 audit block
```

---

## Key Features

1. **Live AI Decision Engine**: Uses Groq LLMs (`llama-3.1-8b-instant`) to parse transaction telemetry, identify root causes, and suggest tailored recovery messaging.
2. **Policy Guardian Safety Boundary**: Hard-coded Python safety rules. If a case exceeds ₹1,00,000 or AI confidence is low, it automatically routes to a human in the loop.
3. **Expected Net Recovery Optimization**: Ranks recovery strategies mathematically:
   $$\text{Expected Net Recovery} = P_{\text{recovery}} \times (\text{Amount} - \text{Discount}) - \text{Operational Cost}$$
4. **Real-Time SSE Telemetry**: Control Tower updates live over Server-Sent Events without manual page refreshes.
5. **Tamper-Evident SHA-256 Hash Chain**: Every state transition links cryptographically to the previous event hash. The UI includes an on-demand audit verification engine.
6. **Native Razorpay Ingestion**: Verifies `X-Razorpay-Signature` via HMAC-SHA256 and auto-reconciles payment confirmation webhooks.

---

## Quick Start (How to Run Locally)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm

---

### 2. Backend Setup & Run

Open a terminal in the project root:

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file from the example
cp .env.example .env
```

Your `.env` should contain:
```env
APP_ENV=development
DATABASE_URL=sqlite:///./recoverypilot.db
RAZORPAY_API_KEY=rzp_test_your_key_id
RAZORPAY_API_SECRET=your_key_secret
RAZORPAY_WEBHOOK_SECRET=razorpay_webhook_secret_demo
GROQ_API_KEY=gsk_your_groq_api_key
AI_MODEL=llama-3.1-8b-instant
```

Start the FastAPI backend server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

* API Docs (Swagger UI) will be live at: **http://127.0.0.1:8000/docs**

---

### 3. Frontend Setup & Run

Open a second terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```

* The React Control Tower will be live at: **http://localhost:5173**

---

## Running Automated Tests

To run the complete backend test suite (59 unit & integration tests):

```bash
cd backend
venv\Scripts\pytest -v
```

To run a production frontend build check:

```bash
cd frontend
npm run build
```

---

## Interactive Demo Scenarios

Once both servers are running, head to `http://localhost:5173/demo` to try the 6 interactive scenarios:

| Scenario | What It Demonstrates |
| :--- | :--- |
| **Scenario 1: Payment Recovery** | AI diagnosis, strategy EV ranking, payment link dispatch, and reconciliation. |
| **Scenario 2: Checkout Abandonment** | Recovery link with bounded 5% discount incentive. |
| **Scenario 3: Policy Guardian Block** | Case reaching max retry limits (2/2) blocked automatically. |
| **Scenario 4: High-Value Escalation** | ₹2,50,000 transaction routed to Human Approval Queue (`/approval-queue`). |
| **Scenario 5: AI Timeout Fallback** | Safe deterministic fallback when LLM exceeds latency thresholds. |
| **Scenario 6: Webhook Closed-Loop** | Real-time `payment_link.paid` webhook updating the Control Tower via SSE. |

---

## Tech Stack

* **Backend**: Python 3.11, FastAPI, SQLAlchemy, SQLite (Dev) / PostgreSQL (Prod), Pydantic v2, Uvicorn
* **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6
* **AI Layer**: Groq Inference API (`llama-3.1-8b-instant`), Gemini Live fallback
* **Payments**: Razorpay Test Mode REST API, HMAC-SHA256 Webhook Verification
* **Testing**: Pytest, TestClient, EventSource browser streaming
