# ShopGuard AI Checklist

Each phase must be completed and verified before moving to the next phase.

## Phase 0: Planning Files and Repo Foundation

- [x] Create `IMPLEMENTATION.md`.
- [x] Create `CHECKLIST.md`.
- [x] Create `backend/` foundation folder.
- [x] Create `frontend/` foundation folder.
- [x] Create `data/mock_shopify/` foundation folder.
- [x] Create `scripts/` foundation folder.
- [x] Create `tests/` foundation folder.
- [x] Create `docs/` foundation folder.
- [x] Avoid adding backend code, frontend code, dependencies, or AI logic in Phase 0.

## Phase 1: Backend Skeleton and Configuration

- [x] Add FastAPI app entrypoint.
- [x] Add Pydantic settings.
- [x] Add PostgreSQL database configuration.
- [x] Add SQLModel session dependency.
- [x] Add health check endpoint.
- [x] Add `.env.example`.
- [x] Verify backend starts.
- [x] Verify `/health` returns success.

## Phase 2: Mock Shopify Dataset and Database Models

- [x] Add mock product data.
- [x] Add mock policy data.
- [x] Add mock order seed data.
- [x] Add product and variant models.
- [x] Add order and order item models.
- [x] Add log models.
- [x] Add repeatable seed script.
- [ ] Verify database records are created correctly.

## Phase 3: RAG Ingestion Pipeline

- [x] Add product chunking.
- [x] Add policy chunking.
- [x] Add ChromaDB collection setup.
- [x] Add metadata-rich document chunks.
- [x] Add ingestion script.
- [ ] Verify product retrieval.
- [ ] Verify policy retrieval.
- [x] Verify citation metadata is available.

## Phase 4: Grounded RAG Chat Endpoint

- [x] Add `POST /api/chat`.
- [x] Add product and policy route handling.
- [x] Add retrieval-backed prompt construction.
- [x] Add Groq grounded response generation.
- [x] Add citations to responses.
- [x] Add safe unknown-answer behavior.
- [x] Verify grounded product answers.
- [x] Verify grounded policy answers.
- [x] Verify unsupported questions do not hallucinate.

## Phase 5: Deterministic Transaction Engine

- [x] Add tool route detection.
- [x] Add `track_order` schema.
- [x] Add `cancel_order` schema.
- [x] Add `request_refund` schema.
- [x] Add backend order tracking logic.
- [x] Add backend order cancellation logic.
- [x] Add backend refund request logic.
- [x] Add tool execution logging.
- [x] Verify valid order tracking.
- [x] Verify invalid order/email handling.
- [x] Verify eligible cancellation.
- [x] Verify ineligible cancellation.
- [x] Verify refund request behavior.

## Phase 6: Interaction Logging and Evaluation

- [x] Add interaction logging.
- [x] Add retrieved context logging.
- [x] Add tool execution result logging.
- [x] Add evaluation log storage.
- [x] Add groundedness scoring script.
- [x] Verify RAG interactions are logged.
- [x] Verify tool interactions are logged.
- [x] Verify evaluation script creates scores.

## Phase 7: Streamlit Frontend

- [ ] Add Streamlit app shell.
- [ ] Add chat panel.
- [ ] Add developer console panel.
- [ ] Display selected route.
- [ ] Display retrieved context.
- [ ] Display citations.
- [ ] Display tool JSON payload.
- [ ] Display deterministic tool result.
- [ ] Display evaluation score when available.
- [ ] Verify product and policy questions from UI.
- [ ] Verify order actions from UI.

## Phase 8: Quality Hardening

- [ ] Add unit tests.
- [ ] Add API tests.
- [ ] Add retrieval tests.
- [ ] Add tool business-rule tests.
- [ ] Add README setup instructions.
- [ ] Add clean error handling.
- [ ] Verify full test suite passes.
- [ ] Verify fresh setup flow.
- [ ] Verify final demo behavior.
