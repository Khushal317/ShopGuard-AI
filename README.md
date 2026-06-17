<p align="center">
  <h1 align="center">🛡️ ShopGuard AI</h1>
  <p align="center">
    <strong>A Grounded AI Customer Support Assistant for E-Commerce</strong>
  </p>
  <p align="center">
    <em>Retrieval-Augmented Generation · Deterministic Tool Execution · Full Observability</em>
  </p>
  <p align="center">
    <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-▶-brightgreen?style=for-the-badge" alt="Quick Start"></a>
    <a href="#-demo-prompts"><img src="https://img.shields.io/badge/Demo-💬-blue?style=for-the-badge" alt="Demo"></a>
    <a href="#-api-reference"><img src="https://img.shields.io/badge/API-📡-orange?style=for-the-badge" alt="API"></a>
  </p>
</p>

---

## 📋 Table of Contents

- [The Real-World Problem](#-the-real-world-problem)
- [Our Solution](#-our-solution)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [File Structure](#-file-structure)
- [Quick Start](#-quick-start)
- [Running the Application](#-running-the-application)
- [Demo Prompts](#-demo-prompts)
- [API Reference](#-api-reference)
- [How the RAG Route Works](#-how-the-rag-route-works)
- [How the Tool Route Works](#-how-the-tool-route-works)
- [Developer Console](#-developer-console)
- [Dataset](#-dataset)
- [Testing](#-testing)
- [Evaluation & Observability](#-evaluation--observability)
- [Environment Configuration](#-environment-configuration)
- [Why This Is More Than a Chatbot](#-why-this-is-more-than-a-chatbot)

---

## 🚨 The Real-World Problem

E-commerce customer support is broken. Stores are flooded with thousands of repetitive questions every day:

> *"Does this jacket come in brown?"*
> *"What is your return policy?"*
> *"Where is my order?"*
> *"Can you cancel my order?"*
> *"I want a refund."*

Traditional chatbots fail at this in two critical ways:

### ❌ Problem 1: Hallucinated Knowledge

Generic AI chatbots **invent** answers. They'll fabricate prices, make up stock availability, quote nonexistent return windows, or describe products that don't exist. In e-commerce, a hallucinated answer isn't just wrong — it's a **liability**. A customer told the wrong return policy can become a legal dispute. A fabricated price can force the store to honor it.

### ❌ Problem 2: Unsafe Order Actions

Even worse, chatbots that claim to "handle orders" often just **generate text that looks like a confirmation**. They'll say *"Your order has been cancelled"* without actually cancelling anything. Or they'll claim a refund was processed when no backend system was ever called. The customer thinks the action happened; the store has no record of it.

### The Core Challenge

These are fundamentally **two different problems** that require two different solutions:

| Question Type | What's Needed | What Goes Wrong Without It |
|---|---|---|
| **Knowledge questions** *(products, policies)* | Grounded answers from real store data | Hallucinated prices, fake stock, wrong policies |
| **Transaction questions** *(orders, refunds)* | Validated backend execution | Fake confirmations, no actual database changes |

A single naive prompt-to-response pipeline cannot solve both. **ShopGuard AI can.**

---

## 💡 Our Solution

ShopGuard AI uses a **dual-route architecture** that separates *knowing* from *doing*:

```
┌─────────────────────────────────────────────────────────┐
│                     User Message                        │
│           "Cancel order #9982 for maya@..."              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Route Detector │
              │  (Keyword +     │
              │   Pattern Match)│
              └───────┬────────┘
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
  ┌─────────────────┐   ┌──────────────────┐
  │  🧠 Knowledge   │   │  🔧 Transaction  │
  │     Route       │   │     Route        │
  │                 │   │                  │
  │ • Search chunks │   │ • Extract params │
  │ • Retrieve      │   │ • Validate with  │
  │   context       │   │   Pydantic       │
  │ • Generate from │   │ • Execute in DB  │
  │   data ONLY     │   │ • Return real    │
  │ • Cite sources  │   │   result         │
  │ • Score ground- │   │ • Log execution  │
  │   edness        │   │                  │
  └─────────────────┘   └──────────────────┘
           │                     │
           ▼                     ▼
  ┌─────────────────────────────────────────┐
  │        Grounded, Auditable Response     │
  │    with Citations or Tool Results       │
  └─────────────────────────────────────────┘
```

### 🧠 Route 1: Knowledge Retrieval Engine

For product and policy questions, the system:

1. **Chunks** the product catalog and policy documents into searchable knowledge units
2. **Searches** using TF-IDF based retrieval with typo tolerance and fuzzy matching
3. **Retrieves** only the relevant context (product details, policy sections)
4. **Generates** an answer using **only** the retrieved context — never from parametric memory
5. **Cites** every source so the answer can be audited
6. **Scores** groundedness to measure how well the answer is supported by the data

### 🔧 Route 2: Deterministic Transaction Engine

For order actions, the system:

1. **Detects** the order intent (track, cancel, refund) using pattern matching
2. **Extracts** structured parameters (order ID, email, refund reason)
3. **Validates** inputs with Pydantic schemas — no malformed requests reach the database
4. **Executes** business logic directly in the FastAPI backend against SQLModel tables
5. **Returns** the actual database result — not generated text
6. **Logs** every tool execution with an audit trail

> **The key insight:** The AI can *explain* store knowledge, but only the **backend** can *perform* order actions. This separation is what makes ShopGuard AI safe for production.

---

## 🏗️ Architecture

```
User Message
    │
    ▼
Streamlit Frontend ─────────────────────────────────────┐
    │                                                    │
    ▼                                                    │
FastAPI /api/chat                                        │
    │                                                    │
    ├──► Route Detector                                  │
    │       │                                            │
    │       ├── Tool keywords found?                     │
    │       │       │                                    │
    │       │       ├──► YES ─► Tool Route               │
    │       │       │           │                        │
    │       │       │           ├── Extract parameters   │
    │       │       │           ├── Pydantic validation  │
    │       │       │           ├── SQLModel DB query    │
    │       │       │           ├── Business rule check  │
    │       │       │           ├── Execute action       │
    │       │       │           └── Return result + log  │
    │       │       │                                    │
    │       │       └──► NO ──► Knowledge keywords?      │
    │       │                       │                    │
    │       │                       ├── YES ─► RAG Route │
    │       │                       │   ├── Search KB    │
    │       │                       │   ├── Retrieve ctx │
    │       │                       │   ├── Generate ans │
    │       │                       │   ├── Cite sources │
    │       │                       │   └── Score + log  │
    │       │                       │                    │
    │       │                       └── NO ─► Unknown    │
    │       │                           └── Safe refusal │
    │       │                                            │
    │       └──► Interaction Logging ◄───────────────────┘
    │                                                    
    ▼                                                    
Developer Console (Streamlit)                            
    ├── Route indicator                                  
    ├── Retrieved context viewer                         
    ├── Citation inspector                               
    ├── Tool call debugger                               
    ├── Groundedness score                               
    └── Raw JSON response                                
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **🎯 Grounded Answers** | Product and policy responses generated exclusively from retrieved store data, never hallucinated |
| **📎 Source Citations** | Every knowledge answer includes traceable citations back to the exact data source |
| **🛑 Safe Refusal** | Unsupported questions get `"I don't know from the available store data"` instead of fabricated answers |
| **📦 Order Tracking** | Real database lookups for order status, tracking numbers, and item details |
| **❌ Order Cancellation** | Business-rule-enforced cancellation (only `processing` orders can be cancelled) |
| **💰 Refund Requests** | Schema-validated refund flow (only `delivered` orders with no existing refund are eligible) |
| **🔍 Typo Tolerance** | Fuzzy matching handles misspellings like `"lether jackets"` → `"leather jackets"` |
| **🧩 Mixed Queries** | Handles combined questions like *"Does the jacket come in brown and what's the return policy?"* |
| **📊 Groundedness Scoring** | Automated evaluation of RAG answer quality against source context |
| **📝 Interaction Logging** | Full audit trail: query, route, context, response, tool calls, and scores |
| **🖥️ Developer Console** | Streamlit-based transparency dashboard for inspecting every decision the system makes |
| **✅ Pydantic Schemas** | Strict validation across all API boundaries, tool contracts, and data models |
| **🗃️ SQLModel ORM** | Type-safe database models for products, variants, orders, logs, and tool executions |
| **🧪 Pytest Coverage** | Automated tests for API behavior, retrieval accuracy, and order business rules |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | FastAPI | Chat, health, and order endpoints with auto-generated Swagger docs |
| **Data Models** | SQLModel | Typed database tables combining SQLAlchemy + Pydantic |
| **Validation** | Pydantic v2 | Strict request/response/tool schemas with model validation |
| **Local Database** | SQLite | Zero-config local demo mode |
| **Production DB** | PostgreSQL (via `psycopg`) | Production-ready database path |
| **Retrieval** | TF-IDF + Fuzzy Matching | Lightweight RAG retrieval without native build dependencies |
| **Vector DB** | ChromaDB-ready | Ingestion code ready for production vector store |
| **LLM Provider** | Groq (LLaMA 3.3 70B) | Optional enhanced answer generation with grounding constraints |
| **Frontend** | Streamlit | Customer chat UI + developer console |
| **Testing** | Pytest | API, retrieval, and business-rule test suites |
| **Email Validation** | `email-validator` | RFC-compliant email validation for order actions |
| **HTTP Client** | HTTPX | Async-ready HTTP client for service communication |

---

## 📁 File Structure

```
ShopGuard AI/
│
├── 📂 backend/                          # FastAPI backend application
│   ├── 📂 app/
│   │   ├── 📂 api/                      # API route handlers
│   │   │   ├── chat.py                  # POST /api/chat — main assistant endpoint
│   │   │   ├── health.py                # GET /health — backend health check
│   │   │   └── orders.py               # GET /api/orders — order inspection
│   │   │
│   │   ├── 📂 core/                     # Application configuration
│   │   │   └── config.py               # Pydantic settings, env vars, DB config
│   │   │
│   │   ├── 📂 db/                       # Database layer
│   │   │   └── session.py              # SQLModel engine factory & session DI
│   │   │
│   │   ├── 📂 models/                   # SQLModel database tables
│   │   │   ├── log.py                  # InteractionLog, RetrievedContextLog,
│   │   │   │                           #   ToolExecutionLog, EvaluationLog
│   │   │   ├── order.py                # Order, OrderItem tables + status enums
│   │   │   └── product.py             # Product, ProductVariant tables
│   │   │
│   │   ├── 📂 schemas/                  # Pydantic validation schemas
│   │   │   ├── chat.py                 # ChatRequest, ChatResponse, Citation,
│   │   │   │                           #   RetrievedContext, ChatRoute
│   │   │   ├── evaluation.py           # GroundednessScore schema
│   │   │   ├── health.py              # HealthResponse schema
│   │   │   ├── knowledge.py           # KnowledgeChunk, KnowledgeSearchResult,
│   │   │   │                           #   ChunkMetadata, SourceType
│   │   │   ├── log.py                 # Logging schemas
│   │   │   ├── order.py               # OrderAction, ToolCallResult,
│   │   │   │                           #   RefundRequest, OrderActionResponse
│   │   │   └── product.py             # ProductSeed, VariantSeed schemas
│   │   │
│   │   ├── 📂 services/                # Core business logic
│   │   │   ├── evaluation.py           # Groundedness scoring engine
│   │   │   ├── interaction_logging.py  # Interaction persistence & audit trail
│   │   │   ├── knowledge_ingestion.py  # Product/policy chunking & search
│   │   │   ├── local_embeddings.py     # TF-IDF local embedding fallback
│   │   │   ├── order_actions.py        # track_order, cancel_order, request_refund
│   │   │   ├── order_tool_router.py    # Tool detection & parameter extraction
│   │   │   └── rag_chat.py            # Main routing engine: RAG + Tool + Unknown
│   │   │
│   │   └── main.py                     # FastAPI application factory
│   │
│   └── requirements.txt                # Backend Python dependencies
│
├── 📂 frontend/                         # Streamlit frontend application
│   ├── streamlit_app.py                # Chat UI + Developer Console
│   └── requirements.txt               # Frontend Python dependencies
│
├── 📂 data/                             # Mock Shopify-style dataset
│   └── 📂 mock_shopify/
│       ├── products.json               # 20 products with variants (color, size, stock, price)
│       ├── orders.json                 # 20 orders with statuses and tracking
│       └── policies.md                 # Shipping, return, and refund policies
│
├── 📂 scripts/                          # Utility & maintenance scripts
│   ├── seed_database.py                # Repeatable demo database seeding
│   ├── ingest_knowledge_base.py        # ChromaDB vector ingestion path
│   └── evaluate_groundedness.py        # Batch evaluation for saved interactions
│
├── 📂 tests/                            # Pytest test suite
│   ├── conftest.py                     # Test DB fixtures & session management
│   ├── test_api.py                     # API endpoint behavior tests
│   ├── test_order_actions.py           # Order business rule tests
│   └── test_retrieval.py              # RAG retrieval & chunk accuracy tests
│
├── 📂 docs/                             # Documentation assets
│
├── .env.example                        # Safe environment variable template
├── .gitignore                          # Git ignore rules
├── CHECKLIST.md                        # Phase-by-phase completion checklist
├── IMPLEMENTATION.md                   # Detailed implementation plan
├── knowledge.md                        # Interview prep & project explanation notes
└── README.md                           # ← You are here
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (tested on Python 3.13)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Khushal317/ShopGuard-AI.git
cd ShopGuard-AI
```

### 2. Create Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r backend\requirements.txt
pip install -r frontend\requirements.txt
```

### 4. Configure Environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your settings. At minimum, set `DATABASE_URL`:

```env
# For local demo (SQLite):
DATABASE_URL=sqlite:///./demo.db

# For production (PostgreSQL):
# DATABASE_URL=postgresql+psycopg://shopguard:shopguard@localhost:5432/shopguard_ai

# Optional: Enable LLM-enhanced answers
# GROQ_API_KEY=your_groq_api_key_here
# GROQ_MODEL=llama-3.3-70b-versatile
```

### 5. Seed the Database

```powershell
$env:DATABASE_URL = "sqlite:///./demo.db"
python scripts\seed_database.py
```

---

## ▶️ Running the Application

### Start the Backend

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///../demo.db"
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify it's running: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Start the Frontend (in a second terminal)

```powershell
$env:SHOPGUARD_API_BASE_URL = "http://127.0.0.1:8000"
.venv\Scripts\python -m streamlit run frontend\streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open the app: [http://127.0.0.1:8501](http://127.0.0.1:8501)

---

## 💬 Demo Prompts

Try these prompts to see ShopGuard AI in action:

### 🧠 Knowledge Route — Product Questions

```
give me info about Aster Leather Jacket - Brown / M
```
> ✅ Returns exact product details with variant info and citations

```
give me info on lether jackets
```
> ✅ Typo-tolerant — correctly matches "leather jackets" despite misspelling

```
Does the leather jacket come in brown and what is the return policy?
```
> ✅ Mixed query — returns both product variant info AND policy details

### 📜 Knowledge Route — Policy Questions

```
what is your return policy?
```
> ✅ Returns the exact return policy from store data with source citation

```
how long does shipping take?
```
> ✅ Returns shipping timeframes from the policies dataset

### 🔧 Tool Route — Order Actions

```
Track order #9982 for maya@example.com
```
> ✅ Database lookup returns real order status and tracking number

```
Cancel order #9982 for maya@example.com
```
> ✅ Business rules enforced — only `processing` orders can be cancelled

```
Request refund for order #10044 for sofia@example.com because changed mind
```
> ✅ Validated refund flow — only `delivered` orders with no existing refund are eligible

### 🛑 Safe Refusal — Unsupported Questions

```
Who won the world cup?
```
> Returns: *"I don't know from the available store data."*

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns backend status |
| `POST` | `/api/chat` | Main assistant endpoint — accepts `{ "message": "..." }` |
| `GET` | `/api/orders` | Inspect all seeded orders in the database |
| `GET` | `/docs` | Auto-generated FastAPI Swagger documentation |

### `POST /api/chat` — Request

```json
{
  "message": "Does the leather jacket come in brown?"
}
```

### `POST /api/chat` — Response (Knowledge Route)

```json
{
  "route": "rag",
  "answer": "Yes. Aster Leather Jacket is available in Brown / S — $179.99, stock 12; Brown / M — $179.99, stock 8.",
  "citations": [
    {
      "source_type": "product",
      "source_file": "products.json",
      "source_id": "PROD-1001",
      "label": "Source: products.json, SKU PROD-1001"
    }
  ],
  "retrieved_context": [...],
  "evaluation": {
    "groundedness_score": 1.0,
    "is_grounded": true
  }
}
```

### `POST /api/chat` — Response (Tool Route)

```json
{
  "route": "tool",
  "answer": "Order found.",
  "tool_call": {
    "tool_name": "track_order",
    "order_id": "9982",
    "email": "maya@example.com"
  },
  "tool_result": {
    "tool_name": "track_order",
    "result_code": "order_found",
    "message": "Order found.",
    "order_id": "9982",
    "order_status": "shipped",
    "tracking_number": "TRK-998200",
    "audit_id": 1
  }
}
```

---

## 🧠 How the RAG Route Works

```
User: "give me info on lether jackets"
           │
           ▼
   ┌───────────────┐
   │ Normalize Query │ ──► "leather jacket" (typo corrected)
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Search KB      │ ──► TF-IDF + fuzzy match against knowledge chunks
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Filter Results │ ──► Product-type filtering, exact SKU matching
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Build Answer   │ ──► Generated ONLY from retrieved context
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Add Citations  │ ──► Source file, SKU, section references
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Score          │ ──► Groundedness score: 0.0 → 1.0
   └───────┬───────┘
           ▼
   ┌───────────────┐
   │ Log & Return   │ ──► Full interaction logged for audit
   └───────────────┘
```

**Key design decisions:**

- **Deterministic-first:** Direct product/policy answers are built without calling an LLM when possible
- **LLM-optional:** If a Groq API key is configured, complex queries get LLM-enhanced answers — still constrained to retrieved context
- **Typo map:** Common misspellings are mapped before routing (`lether` → `leather`, `sneekers` → `sneakers`)
- **Mixed query support:** Product-type and policy tokens are detected separately, allowing both to be answered in one response

---

## 🔧 How the Tool Route Works

### Supported Tools

| Tool | Trigger | Required Fields | Business Rules |
|---|---|---|---|
| `track_order` | "track", "where is", "status of" | `order_id`, `email` | Order + email must match |
| `cancel_order` | "cancel" | `order_id`, `email` | Only `processing` orders |
| `request_refund` | "refund" | `order_id`, `email`, `reason` | Only `delivered` + no existing refund |

### Business Rule Enforcement

```
Cancel Order #9982
    │
    ├── Order exists? ──► NO ──► "No order matched that order ID and email."
    │
    ├── Email matches? ──► NO ──► "No order matched that order ID and email."
    │
    ├── Status = processing? ──► NO ──► "This order cannot be cancelled
    │                                     because it is no longer processing."
    │
    └── YES ──► Status → cancelled
               └── Return confirmation + audit log
```

**Why this matters:** The AI never "claims" an order was cancelled. The backend either performs the action and confirms it, or rejects it with a specific reason. There's no gap between what the customer is told and what actually happened.

---

## 🖥️ Developer Console

The Streamlit frontend has two views:

### 1. Customer Chat (`ShopGuard AI`)
- Clean conversational interface
- Product cards with variant details
- Policy answer formatting
- Order result cards with status and tracking
- Citation display

### 2. Developer Console
- **Route indicator** — Which engine handled the query (RAG / Tool / Unknown)
- **Retrieved context** — The exact knowledge chunks that were searched and matched
- **Citation inspector** — Source files, SKUs, and sections cited in the answer
- **Tool call debugger** — Tool name, extracted parameters, and execution result
- **Groundedness score** — Numerical evaluation of answer quality (0.0–1.0)
- **Raw JSON viewer** — Complete backend response for debugging

> The developer console exists because grounded AI systems need **observability**. It lets an engineer verify that the assistant is using data, tools, and schemas — not blindly generating text.

---

## 📦 Dataset

The project uses a mock Shopify-style dataset in `data/mock_shopify/`.

### Products — `products.json`

**20 products** with realistic e-commerce fields:

| Field | Example |
|---|---|
| Product SKU | `PROD-1001` |
| Title | `Aster Leather Jacket` |
| Category | `Jackets` |
| Description | Full product description |
| Base Price | `$179.99` |
| Variants | 2–4 per product (color, size, stock, price) |

**Product categories:** Jackets, Sneakers, Totes, Shirts, Watches, Wallets, Coats, Dresses, Hoodies, Caps, Scarves, Belts, Sunglasses, Boots, Backpacks

### Orders — `orders.json`

**20 mock orders** covering all possible states:

| Field | Values |
|---|---|
| Order IDs | `#9980` – `#10044` |
| Statuses | `pending`, `processing`, `shipped`, `delivered`, `cancelled` |
| Refund Statuses | `not_requested`, `requested`, `refunded` |
| Tracking Numbers | Format: `TRK-XXXXXX` |

### Policies — `policies.md`

Three policy sections, each chunked separately for targeted retrieval:

- **Shipping Policy** — Free shipping over $50, standard 5–7 days, express 2–3 days
- **Return Policy** — 30-day window, items must be unused with tags
- **Refund Policy** — Processed within 5–7 business days to original payment method

---

## 🧪 Testing

Run the full test suite:

```powershell
.venv\Scripts\python -m pytest
```

### Test Coverage

| Test File | What It Covers |
|---|---|
| `test_api.py` | Health endpoint, chat endpoint (all routes), response schema validation |
| `test_retrieval.py` | Chunk creation, search accuracy, typo tolerance, exact SKU filtering, policy retrieval, mixed queries |
| `test_order_actions.py` | Track/cancel/refund with valid inputs, email mismatch, status eligibility, business rule enforcement, tool execution logging |

### Key Test Scenarios

- ✅ Product queries return correct variants and prices
- ✅ Typo queries (`"lether jackets"`) still find the right products
- ✅ Policy queries return the correct policy section
- ✅ Mixed queries return both product and policy results
- ✅ Unsupported queries return safe refusal message
- ✅ Order tracking returns correct status and tracking number
- ✅ Cancellation is rejected for non-`processing` orders
- ✅ Refund is rejected for non-`delivered` orders
- ✅ Email mismatch returns `order_not_found`
- ✅ Tool executions are logged with audit IDs

---

## 📊 Evaluation & Observability

### Groundedness Scoring

Every RAG answer is automatically scored for groundedness:

```
Score = (claims supported by context) / (total claims in answer)
```

- **1.0** — Fully grounded: every claim is supported by retrieved context
- **0.0** — Not grounded: answer contains unsupported claims
- Scores are logged per-interaction and visible in the developer console

### Interaction Logging

Every interaction is persisted with:

| Logged Data | Purpose |
|---|---|
| User query | What was asked |
| Selected route | How it was routed (RAG / Tool / Unknown) |
| Retrieved context | What data was found |
| Generated answer | What was returned |
| Citations | What sources were cited |
| Tool calls & results | What actions were executed |
| Groundedness score | How well the answer was supported |
| Timestamps & latency | Performance tracking |

---

## ⚙️ Environment Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | Database connection string (`sqlite:///./demo.db` for local) |
| `GROQ_API_KEY` | No | — | Groq API key for LLM-enhanced answers |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `CHROMA_PERSIST_DIR` | No | `./chroma_store` | ChromaDB storage directory |
| `CHROMA_COLLECTION_NAME` | No | `shopguard_knowledge` | ChromaDB collection name |

> **Note:** The system works fully without a Groq API key. Without it, answers are built deterministically from retrieved context. With it, complex queries get LLM-enhanced responses that are still constrained to the retrieved data.

---

## 🏆 Why This Is More Than a Chatbot

ShopGuard AI is **not** a prompt wrapped in a UI. It demonstrates real AI engineering:

| Capability | What It Proves |
|---|---|
| **Dual-route architecture** | Different problem types need different solutions |
| **Retrieval-augmented generation** | Answers are grounded in data, not hallucinated |
| **Deterministic tool execution** | Order actions happen in the backend, not in text |
| **Pydantic schemas everywhere** | Type safety across API, tools, and data contracts |
| **SQLModel ORM** | Production-quality database models |
| **Business rule enforcement** | Real-world constraints (cancellation windows, refund eligibility) |
| **Source citations** | Every answer is auditable |
| **Safe refusal** | The system knows what it doesn't know |
| **Groundedness scoring** | Automated evaluation of answer quality |
| **Interaction logging** | Full observability for debugging and auditing |
| **Developer console** | Transparency into every decision |
| **Automated test suite** | Verified behavior for API, retrieval, and business rules |
| **Phase-based development** | Structured, documented engineering process |

> This structure mirrors how a real AI assistant should be built: **flexible where conversation is useful, deterministic where correctness matters.**

---

## 📄 License

This project is built as a portfolio demonstration of AI engineering principles.

---

<p align="center">
  Built with ❤️ using FastAPI · Streamlit · SQLModel · Pydantic
</p>
