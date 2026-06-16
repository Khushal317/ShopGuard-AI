# ShopGuard AI Implementation Plan

## 1. Project Goal

ShopGuard AI is a grounded AI assistant for an e-commerce storefront. It will answer product and policy questions using retrieval-augmented generation, and it will handle order actions through deterministic tool execution backed by PostgreSQL.

The project will be built phase by phase. Each phase must be implemented, verified, and checked off in `CHECKLIST.md` before the next phase starts.

## 2. Core Architecture

The system has two main routes:

1. Knowledge Retrieval Engine
   - Handles product and policy questions.
   - Retrieves exact context from the local knowledge base.
   - Generates grounded answers with citations.
   - Refuses to answer when the retrieved context is insufficient.

2. Deterministic Transaction Engine
   - Handles rigid order actions such as tracking, cancellation, and refund requests.
   - Uses Groq tool calling only to extract structured parameters.
   - Uses Pydantic schemas to validate tool inputs.
   - Executes all business logic in the FastAPI backend.
   - Returns deterministic database-backed results.

## 3. Tech Stack Decisions

- Backend: FastAPI
- Frontend: Streamlit
- Database: PostgreSQL
- ORM and typed models: SQLModel
- Validation: Pydantic
- LLM provider: Groq first
- Vector database: ChromaDB
- Embeddings: local/open-source embeddings for v1
- RAG orchestration: simple service layer first, with LangChain or LangGraph added when useful
- Testing: pytest

## 4. Planned Project Structure

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
  tests/

frontend/
  streamlit_app.py

data/
  mock_shopify/
    products.json
    policies.md

scripts/
  seed_database.py
  ingest_knowledge_base.py

docs/
  architecture.md

IMPLEMENTATION.md
CHECKLIST.md
README.md
.env.example
```

This structure is the target shape. Phase 0 only creates the planning files and empty foundation folders. Implementation files will be added in later phases.

## 5. Schema Plan

All important boundaries will use explicit schemas.

Backend request and response schemas:

- `ChatRequest`
- `ChatResponse`
- `Citation`
- `RetrievedContext`
- `OrderActionRequest`
- `OrderActionResponse`
- `ToolCallRequest`
- `ToolCallResult`
- `EvaluationResult`

Database model groups:

- Product and variant records
- Policy source records
- Order and order item records
- Interaction logs
- Retrieved context logs
- Tool execution logs
- Evaluation logs

Tool schemas:

- `track_order(order_id: str, email: str)`
- `cancel_order(order_id: str, email: str)`
- `request_refund(order_id: str, email: str, reason: str | None)`

The LLM may extract parameters, but the backend is the only place where order state can be read or changed.

## 6. Phase Plan

### Phase 0: Planning Files and Repo Foundation

Create:

- `IMPLEMENTATION.md`
- `CHECKLIST.md`
- Empty foundation folders:
  - `backend/`
  - `frontend/`
  - `data/mock_shopify/`
  - `scripts/`
  - `tests/`
  - `docs/`

No backend code, frontend code, dependencies, or AI logic will be added in this phase.

### Phase 1: Backend Skeleton and Configuration

Build the minimal FastAPI foundation.

Add:

- FastAPI app entrypoint.
- Pydantic settings.
- PostgreSQL connection setup.
- SQLModel database session dependency.
- Health check endpoint.
- `.env.example`.

Verify:

- Backend starts.
- `/health` returns success.
- Database configuration loads without exposing secrets.

### Phase 2: Mock Shopify Dataset and Database Models

Add mock e-commerce data and database models.

Add:

- `products.json`
- `policies.md`
- mock order seed data
- SQLModel models for products, variants, orders, order items, and logs
- seed script

Verify:

- Tables can be created.
- Seed script is repeatable.
- Mock records can be queried from PostgreSQL.

### Phase 3: RAG Ingestion Pipeline

Build retrieval data preparation.

Add:

- Product chunking.
- Policy chunking.
- ChromaDB collection setup.
- Metadata-rich document chunks.
- Ingestion script.

Verify:

- Chroma collection is created.
- Product questions retrieve product chunks.
- Policy questions retrieve policy chunks.
- Retrieved chunks include source metadata.

### Phase 4: Grounded RAG Chat Endpoint

Add product and policy answering.

Add:

- `POST /api/chat`.
- RAG route detection for product and policy questions.
- Groq response generation from retrieved context.
- Citation output.
- Unknown-answer behavior when context is insufficient.

Verify:

- Product answers are grounded in mock product data.
- Policy answers are grounded in policy data.
- Mixed questions return both product and policy citations.
- Unsupported questions return a safe unknown response.

### Phase 5: Deterministic Transaction Engine

Add order actions.

Add:

- Tool-calling route detection.
- Pydantic tool argument validation.
- Order tracking.
- Order cancellation.
- Refund request handling.
- Tool execution logging.

Verify:

- Valid order tracking returns database state.
- Invalid order/email pairs fail safely.
- Eligible cancellation updates the database.
- Ineligible cancellation does not update the database.
- Refund requests follow stored policy and order state.

### Phase 6: Interaction Logging and Evaluation

Add quality tracking.

Add:

- Interaction logging.
- Retrieved context logging.
- Tool execution logging.
- Evaluation log storage.
- Groundedness scoring script.

Verify:

- Every chat request creates an interaction log.
- RAG requests store retrieved context.
- Tool requests store deterministic execution records.
- Evaluation script scores saved RAG answers.

### Phase 7: Streamlit Frontend

Add the demo interface.

Add:

- Single-page Streamlit app.
- Chat panel.
- Developer console panel.
- Display for route, retrieved context, citations, tool JSON, deterministic result, and evaluation score.

Verify:

- Product and policy questions work from the UI.
- Order actions work from the UI.
- Developer console updates with real backend data.
- Errors are shown clearly.

### Phase 8: Quality Hardening

Prepare the project to look and behave like a serious medium-level demo.

Add:

- Focused unit tests.
- API tests.
- Retrieval tests.
- Tool business-rule tests.
- README setup instructions.
- Clean error handling.

Verify:

- Test suite passes.
- Fresh setup flow works.
- Demo behavior is consistent.
- `CHECKLIST.md` is fully updated.

## 7. Implementation Rules

- Work one phase at a time.
- Do not add future-phase code early.
- Keep the architecture clean but simple.
- Prefer typed schemas over loose dictionaries.
- Keep order actions deterministic.
- Do not let generated text claim that an order action succeeded.
- Keep RAG answers grounded in retrieved context.
- Log enough developer evidence to prove what happened.
- Update `CHECKLIST.md` only after implementation and verification.

