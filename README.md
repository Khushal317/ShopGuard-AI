# ShopGuard AI

ShopGuard AI is a grounded e-commerce assistant demo with two paths:

- RAG-style product and policy answers with citations.
- Deterministic order actions for tracking, cancellation, and refund requests.

The backend is FastAPI. The frontend is Streamlit. SQLModel is used for typed database access.

## Current Demo Mode

The local demo can run with SQLite so it works without a PostgreSQL setup. PostgreSQL remains the intended production-style database path, but the local `shopguard` credentials must be configured before using it.

ChromaDB integration code exists, but this Windows/Python 3.13 environment cannot install `chroma-hnswlib` without Microsoft C++ Build Tools. Until ChromaDB is available, the app uses the local retrieval fallback.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
.venv\Scripts\python -m pip install -r frontend\requirements.txt
```

Create `.env` from `.env.example` and set values locally. Do not commit real API keys.

## Seed Demo Data

```powershell
$env:DATABASE_URL = "sqlite:///./demo.db"
.venv\Scripts\python scripts\seed_database.py
```

## Run Backend

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///../demo.db"
..\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

## Run Frontend

From the project root:

```powershell
$env:SHOPGUARD_API_BASE_URL = "http://127.0.0.1:8000"
.venv\Scripts\python -m streamlit run frontend\streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Frontend:

```text
http://127.0.0.1:8501
```

## Demo Prompts

Product and policy:

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

Refund:

```text
Request refund for order #10044 for sofia@example.com because changed mind
```

Unknown:

```text
Who won the world cup?
```

## Tests

```powershell
.venv\Scripts\python -m pytest
```
