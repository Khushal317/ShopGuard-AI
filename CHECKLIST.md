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

- [ ] Add product chunking.
- [ ] Add policy chunking.
- [ ] Add ChromaDB collection setup.
- [ ] Add metadata-rich document chunks.
- [ ] Add ingestion script.
- [ ] Verify product retrieval.
- [ ] Verify policy retrieval.
- [ ] Verify citation metadata is available.

## Phase 4: Grounded RAG Chat Endpoint

- [ ] Add `POST /api/chat`.
- [ ] Add product and policy route handling.
- [ ] Add retrieval-backed prompt construction.
- [ ] Add Groq grounded response generation.
- [ ] Add citations to responses.
- [ ] Add safe unknown-answer behavior.
- [ ] Verify grounded product answers.
- [ ] Verify grounded policy answers.
- [ ] Verify unsupported questions do not hallucinate.

## Phase 5: Deterministic Transaction Engine

- [ ] Add tool route detection.
- [ ] Add `track_order` schema.
- [ ] Add `cancel_order` schema.
- [ ] Add `request_refund` schema.
- [ ] Add backend order tracking logic.
- [ ] Add backend order cancellation logic.
- [ ] Add backend refund request logic.
- [ ] Add tool execution logging.
- [ ] Verify valid order tracking.
- [ ] Verify invalid order/email handling.
- [ ] Verify eligible cancellation.
- [ ] Verify ineligible cancellation.
- [ ] Verify refund request behavior.

## Phase 6: Interaction Logging and Evaluation

- [ ] Add interaction logging.
- [ ] Add retrieved context logging.
- [ ] Add tool execution result logging.
- [ ] Add evaluation log storage.
- [ ] Add groundedness scoring script.
- [ ] Verify RAG interactions are logged.
- [ ] Verify tool interactions are logged.
- [ ] Verify evaluation script creates scores.

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
