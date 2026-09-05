# RecoveryPilot AI Architecture

## Current Phase 1 Architecture
The Phase 1 architecture establishes the foundational infrastructure required to support the future AI Control Tower. It is designed to be highly modular, scalable, and independent.

### Frontend
- **Framework**: React.js with Vite
- **Language**: TypeScript (Strict Mode)
- **Styling**: Tailwind CSS
- **Design Pattern**: The frontend utilizes a component-based architecture with separated concerns:
  - `components/`: Reusable UI elements (e.g., Status indicators, layout wrappers).
  - `pages/`: High-level page components (e.g., Dashboard).
  - `hooks/`: Custom React hooks for data fetching and state management.
  - `api/`: Centralized API client for all backend communication to prevent scattered fetch calls.

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Design Pattern**: Domain-Driven Design (DDD) inspired modular monolith.
  - `api/`: Route handlers and controllers.
  - `core/`: Application configuration, environment variables, structured logging, and database initialization.
  - `domain/ & models/ & schemas/`: Data representation, ORM models, and Pydantic validation schemas.
  - `services/ & repositories/`: Business logic and database access layers.
  - Future AI logic will live in `agents/`, `guardian/`, and `simulation/`.

### Database
- **Current**: SQLite (for local development speed and simplicity).
- **ORM**: SQLAlchemy.
- **Migrations**: Alembic.
- **Future Proofing**: The database connection string is completely environment-driven. Transitioning to PostgreSQL requires no application code changes, only an updated `DATABASE_URL` in the `.env` file.

---

## Future Architecture Concepts

### Agent Architecture
RecoveryPilot AI will not be a generic chatbot. It will utilize specialized AI agents to handle the `DETECT → DIAGNOSE → SIMULATE` loop. The AI will evaluate a recovery case (e.g., a failed payment), hypothesize the root cause, and simulate the expected recovery rate of various counterfactual strategies.

### Policy Guardian Concept
**Crucial Principle: AI will never directly execute financial actions.**

Because AI can be non-deterministic or hallucinate, every action proposed by the Strategy Simulator is passed to the **Policy Guardian**.
The Policy Guardian is a purely deterministic, rule-based engine written in Python. It enforces strict compliance, idempotency, stopping rules (e.g., `MAX_MESSAGES = 3`), and financial limits. 

Only actions explicitly returned as `APPROVED` by the Guardian are handed off to the Executor. Actions that fail the Guardian's checks are either `BLOCKED` or flagged as `HUMAN_APPROVAL_REQUIRED`.
