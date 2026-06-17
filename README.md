# ShopGuard AI

ShopGuard AI is a grounded AI customer-support assistant for an e-commerce storefront. It is built to answer product and policy questions from real store data, and to handle sensitive order actions through deterministic backend tools instead of unsafe free-form text generation.

The project is designed as a medium-level, portfolio-ready AI engineering demo. It shows retrieval-augmented generation, structured schemas, transaction-safe tool execution, interaction logging, groundedness scoring, and a Streamlit developer console for transparency.

## Real-World Problem

E-commerce stores receive many repetitive support questions:

- "Does this jacket come in brown?"
- "What is your return policy?"
- "Where is my order?"
- "Can you cancel my order?"
- "Can I request a refund?"

A normal chatbot can answer these questions conversationally, but that is not enough for a real store. The assistant must not invent prices, stock counts, return rules, tracking details, or order status. It also must not claim that an order was cancelled or refunded unless the backend actually performed that action.

This creates two different problems:

1. Knowledge questions need grounded answers from store data.
2. Transaction questions need validated backend execution.

ShopGuard AI solves both by routing the user message to the correct engine.

## Solution

ShopGuard AI uses a two-route architecture:

1. Knowledge Retrieval Engine
   - Used for product and policy questions.
   - Searches the mock Shopify dataset.
   - Retrieves exact product or policy context.
   - Generates an answer only from retrieved context.
   - Returns citations so the answer can be audited.

2. Deterministic Transaction Engine
   - Used for order tracking, cancellation, and refund requests.
   - Extracts structured parameters such as order ID and email.
   - Validates those parameters with Pydantic schemas.
   - Executes business logic in the FastAPI backend.
   - Returns database-backed results instead of hallucinated text.

In simple terms: the AI can explain store knowledge, but only the backend can perform order actions.

## Architecture

```text
User Message
    |
    v
Streamlit Frontend
    |
    v
FastAPI /api/chat
    |
    +--> Knowledge Route
    |       |
    |       +--> Product and policy chunks
    |       +--> Local retrieval fallback / Chroma-ready ingestion
    |       +--> Grounded answer
    |       +--> Citations and groundedness score
    |
    +--> Tool Route
            |
            +--> Tool parameter extraction
            +--> Pydantic validation
            +--> SQLModel database lookup/update
            +--> Deterministic tool result
```

## Key Features

- Grounded product and policy answers with source citations.
- Safe unknown-answer behavior for unsupported questions.
- Deterministic order tracking, cancellation, and refund request handling.
- Pydantic request, response, tool, and data schemas.
- SQLModel database models for products, variants, orders, logs, and tool executions.
- Mock Shopify-style dataset with 20 products and 20 orders.
- Interaction logging for observability.
- Groundedness scoring for RAG answer quality.
- Streamlit frontend with separate customer chat and developer console views.
- Focused pytest coverage for API behavior, retrieval, and order business rules.

## Tech Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Backend API | FastAPI | Chat, health, and order endpoints |
| Data models | SQLModel | Typed database tables and ORM access |
| Validation | Pydantic | Strict request, response, and tool schemas |
| Local database | SQLite | Easy local demo mode |
| Production-style database path | PostgreSQL-ready config | More realistic deployment option |
| Retrieval | Local lexical/vector-style fallback | Lightweight RAG retrieval without native build issues |
| Vector DB path | ChromaDB-ready code | Future vector store support |
| LLM provider | Groq-compatible chat API | Optional grounded answer generation |
| Frontend | Streamlit | Chat UI and developer console |
| Testing | Pytest | API, retrieval, and business-rule tests |

## Dataset

The project uses a mock Shopify-style dataset in `data/mock_shopify/`.

### Products

File: `data/mock_shopify/products.json`

The products dataset contains 20 products with realistic e-commerce fields:

- product SKU
- title
- category
- description
- base price
- currency
- variants
- variant SKU
- color
- size
- stock
- variant price

Example product types include jackets, sneakers, totes, shirts, watches, wallets, coats, dresses, and accessories. This variety lets the assistant answer practical storefront questions about price, availability, variants, color, size, and stock.

### Policies

File: `data/mock_shopify/policies.md`

The policies file contains store policy sections for:

- shipping
- returns
- refunds

These sections are chunked separately so policy questions can retrieve only the relevant source text.

### Orders

File: `data/mock_shopify/orders.json`

The orders dataset contains 20 mock orders with:

- order ID
- customer email
- customer name
- order status
- refund status
- total amount
- tracking number
- order items

This supports safe demos for tracking, cancellation, refund requests, invalid email/order pairs, and ineligible order states.

## File Structure

```text
ShopGuard AI/
  backend/
    app/
      api/
        chat.py                  # POST /api/chat endpoint
        health.py                # Health check endpoint
        orders.py                # Order inspection endpoints
      core/
        config.py                # Pydantic settings and environment config
      db/
        session.py               # SQLModel engine and session dependency
      models/
        log.py                   # Interaction, retrieved context, tool, evaluation logs
        order.py                 # Order and order item tables
        product.py               # Product and variant tables
      schemas/
        chat.py                  # Chat request/response schemas
        evaluation.py            # Groundedness scoring schemas
        health.py                # Health response schema
        knowledge.py             # Knowledge chunk and retrieval schemas
        log.py                   # Logging schemas
        order.py                 # Order and tool schemas
        product.py               # Product seed schemas
      services/
        evaluation.py            # Groundedness scoring
        interaction_logging.py   # Interaction persistence
        knowledge_ingestion.py   # Product/policy chunking and retrieval
        local_embeddings.py      # Lightweight local embedding fallback
        order_actions.py         # Deterministic order business logic
        order_tool_router.py     # Tool detection and parameter extraction
        rag_chat.py              # Main chat routing and RAG response logic
      main.py                    # FastAPI app factory
    requirements.txt

  data/
    mock_shopify/
      orders.json                # Mock order dataset
      policies.md                # Mock policy dataset
      products.json              # Mock product dataset

  frontend/
    streamlit_app.py             # Streamlit customer chat and developer console
    requirements.txt

  scripts/
    evaluate_groundedness.py     # Evaluation script for saved RAG interactions
    ingest_knowledge_base.py     # ChromaDB ingestion path
    seed_database.py             # Repeatable demo database seeding

  tests/
    conftest.py                  # Test database/session fixtures
    test_api.py                  # API behavior tests
    test_order_actions.py        # Tool business-rule tests
    test_retrieval.py            # RAG and retrieval tests

  CHECKLIST.md                   # Phase checklist
  IMPLEMENTATION.md              # Phase-by-phase implementation plan
  knowledge.md                   # Interview/project explanation notes
  README.md                      # Project overview and setup
  .env.example                   # Safe environment template
  .gitignore
```

## How The RAG Route Works

The RAG route is used for product and policy questions.

Flow:

1. Product JSON and policy Markdown are converted into knowledge chunks.
2. Each chunk receives metadata such as source file, SKU, title, section, and source type.
3. The user query is normalized and searched against the local knowledge base.
4. The best matching chunks are returned as retrieved context.
5. The response is built from retrieved context only.
6. Citations are attached to show exactly where the answer came from.
7. A groundedness score is calculated and logged.

The app also includes ChromaDB ingestion code. In this Windows/Python 3.13 environment, ChromaDB's native dependency can be difficult to install without Microsoft C++ Build Tools, so the current demo uses the local retrieval fallback. The architecture still keeps the vector database path ready for a production-style environment.

## How The Tool Route Works

The tool route is used for order actions.

Supported tools:

- `track_order`
- `cancel_order`
- `request_refund`

Flow:

1. The message is inspected for an order action.
2. The backend extracts required fields such as order ID, email, and refund reason.
3. Pydantic schemas validate the structured tool request.
4. SQLModel queries the database for the matching order.
5. Business rules decide what can happen.
6. The backend returns a deterministic result.
7. Tool execution is logged for inspection.

This prevents the assistant from falsely claiming that an order was cancelled, refunded, or found.

## Developer Console

The Streamlit frontend has two top-level views:

1. ShopGuard AI
   - Customer-facing chat experience.
   - Shows product cards, policy answers, order results, and citations.

2. Developer Console
   - Technical inspection view.
   - Shows route selection, retrieved context, citations, tool calls, tool results, groundedness score, and raw backend JSON.

The developer console exists because grounded AI systems need observability. It lets an interviewer or engineer verify that the assistant is using data, tools, and schemas instead of blindly generating text.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check backend health |
| `POST` | `/api/chat` | Main assistant endpoint |
| `GET` | `/api/orders` | Inspect seeded orders |
| `GET` | `/docs` | FastAPI Swagger documentation |

## Setup

Create and activate a virtual environment from the project root:

```powershell
python -m venv .venv
```

Install backend and frontend dependencies:

```powershell
.venv\Scripts\python -m pip install -r backend\requirements.txt
.venv\Scripts\python -m pip install -r frontend\requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Set local values in `.env`. Do not commit real API keys.

## Seed The Demo Database

For local demo mode, use SQLite:

```powershell
$env:DATABASE_URL = "sqlite:///./demo.db"
.venv\Scripts\python scripts\seed_database.py
```

The seed script loads products and orders from `data/mock_shopify/` and creates repeatable demo data.

## Run The Backend

From the project root:

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///../demo.db"
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Run The Frontend

From the project root in a second terminal:

```powershell
$env:SHOPGUARD_API_BASE_URL = "http://127.0.0.1:8000"
.venv\Scripts\python -m streamlit run frontend\streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open the app:

```text
http://127.0.0.1:8501
```

## Demo Prompts

Product question:

```text
give me info about Aster Leather Jacket - Brown / M
```

Typo-tolerant product question:

```text
give me info on lether jackets
```

Policy question:

```text
what is your return policy?
```

Mixed product and policy question:

```text
Does the leather jacket come in brown and what is the return policy?
```

Order tracking:

```text
Track order #9982 for maya@example.com
```

Cancellation:

```text
Cancel order #9982 for maya@example.com
```

Refund request:

```text
Request refund for order #10044 for sofia@example.com because changed mind
```

Unsupported question:

```text
Who won the world cup?
```

Expected behavior for unsupported questions:

```text
I don't know from the available store data.
```

## Tests

Run the full test suite:

```powershell
.venv\Scripts\python -m pytest
```

Current test coverage includes:

- API endpoint behavior.
- Product and policy chunk creation.
- Local retrieval behavior.
- Exact product query filtering.
- Typo-tolerant retrieval.
- Safe unknown-answer behavior.
- Order tracking rules.
- Cancellation rules.
- Refund request rules.
- Tool execution logging.

## Evaluation

The project includes a simple groundedness scoring flow. It compares generated RAG answers against retrieved context and records whether the answer is supported by the source text.

This is intentionally lightweight for the demo, but it proves the evaluation concept:

- log the user query
- log retrieved context
- log the final answer
- score answer support against context
- expose the score in the developer console

## Environment And Git Notes

The repository intentionally ignores local runtime files:

- `.env`
- `.venv/`
- `*.db`
- `.backend.pid`
- `.frontend.pid`
- logs
- cache folders
- local Chroma store

The safe template `.env.example` is tracked. Real API keys should stay local.

## Why This Project Is More Than A Basic Chatbot

ShopGuard AI is not just a prompt wrapped in a UI. It has real engineering boundaries:

- retrieval for knowledge questions
- deterministic tools for order actions
- typed schemas across API and tool contracts
- database-backed business logic
- citations
- safe refusal behavior
- interaction logs
- groundedness scoring
- frontend developer console
- automated tests
- phase-based implementation documentation

This structure is close to how a real AI assistant should be built: flexible where conversation is useful, deterministic where correctness matters.

## Interview Summary

ShopGuard AI is a grounded e-commerce assistant built with FastAPI, Streamlit, SQLModel, Pydantic, and a mock Shopify dataset. It separates product and policy questions from order actions. Product and policy questions use retrieval with citations, while order tracking, cancellation, and refunds use deterministic backend tools validated by schemas. The project also includes interaction logging, groundedness scoring, tests, and a developer console so the system is explainable and debuggable.
