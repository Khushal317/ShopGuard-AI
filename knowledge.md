# ShopGuard AI Project Knowledge

## 1. What We Built

ShopGuard AI is a grounded AI assistant for an e-commerce storefront. It is designed to answer customer questions about products, store policies, and order actions in a safe and transparent way.

The project has two main capabilities:

1. Product and policy question answering
   - Example: "Does the leather jacket come in brown?"
   - Example: "What is your return policy?"
   - These questions are answered using store data and policy documents.

2. Deterministic order actions
   - Example: "Track order #9982 for maya@example.com"
   - Example: "Cancel order #9982 for maya@example.com"
   - Example: "Request refund for order #10044 for sofia@example.com"
   - These actions are handled by backend tools, not free-form AI text.

The important idea is that we do not use the AI in the same way for every problem. Product and policy questions can use retrieval and natural language. Order actions must be deterministic, validated, and database-backed.

## 2. Why We Built It This Way

An e-commerce support assistant needs to be helpful, but it also needs to be safe.

A normal chatbot may answer confidently even when it does not have the right data. That is risky for a store because it can invent prices, stock, shipping rules, return rules, or even claim that an order was cancelled when no backend action actually happened.

ShopGuard AI avoids that by splitting the system into two routes:

- RAG route for knowledge questions.
- Tool route for transaction/order questions.

This makes the project stronger than a basic chatbot because it has grounding, schemas, deterministic actions, logs, and visibility into what the system is doing.

## 3. High-Level Architecture

The user sends a message through the Streamlit frontend. The frontend calls the FastAPI backend through `/api/chat`.

The backend decides which path to use:

- If the message is about products or policies, it uses retrieval logic.
- If the message is about orders, cancellation, tracking, or refunds, it uses deterministic order tools.
- If the question is outside the known store data, it returns a safe unknown response.

The backend response is shown in two places:

- The main ShopGuard AI chat tab shows the customer-friendly answer.
- The Developer Console tab shows the technical evidence behind the answer.

## 4. Tech Stack

Backend:

- FastAPI for API endpoints.
- SQLModel for database models and typed database access.
- Pydantic for request and response schemas.
- SQLite for local demo mode.
- PostgreSQL-ready configuration for a more production-like setup.

Frontend:

- Streamlit for a simple interactive chat interface.
- Requests for calling the backend API.

AI and retrieval:

- Groq support is wired in for grounded generation when the API key is available.
- Local retrieval fallback is used because ChromaDB has a Windows/Python 3.13 native dependency issue in this environment.
- ChromaDB collection setup code exists for future vector storage.

Testing:

- Pytest for API, retrieval, and business-rule tests.

## 5. Dataset

The project uses a mock Shopify-style dataset. It is small, but designed to represent the important parts of a real e-commerce assistant.

### Products Dataset

File:

```text
data/mock_shopify/products.json
```

It contains product records with:

- SKU
- product title
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

Example products include:

- Aster Leather Jacket
- Cloudstep Everyday Sneaker
- Harbor Canvas Tote

This lets the assistant answer questions like:

- Which products are available?
- Does a product come in a certain color?
- What sizes or variants exist?
- What is the stock count?
- What is the price?

### Policies Dataset

File:

```text
data/mock_shopify/policies.md
```

It contains store policy sections:

- Shipping
- Returns
- Refunds

This lets the assistant answer questions like:

- How long does shipping take?
- What is the return window?
- What items are not returnable?
- When are refunds issued?
- Are shipping fees refundable?

### Orders Dataset

File:

```text
data/mock_shopify/orders.json
```

It contains mock customer orders with:

- order ID
- customer email
- customer name
- order status
- refund status
- total amount
- tracking number
- order items

This enables safe testing of:

- order tracking
- cancellation
- refund requests
- invalid order/email handling

## 6. RAG: How And Why We Used It

RAG means Retrieval-Augmented Generation.

Instead of asking the model to answer from memory, we first retrieve relevant store data, then answer using that retrieved context.

In this project, RAG is used for product and policy questions.

The flow is:

1. Load product and policy data.
2. Convert them into knowledge chunks.
3. Attach metadata to each chunk.
4. Retrieve chunks related to the user query.
5. Build an answer using only the retrieved context.
6. Return citations so we know where the answer came from.

This is important because product and policy answers must be grounded in actual store data. If the answer is not in the dataset, the assistant should say it does not know instead of guessing.

## 7. Retrieval Logic

The retrieval layer builds chunks from:

- product data
- policy sections

Each chunk has metadata such as:

- source type
- source file
- source ID
- product SKU
- product title
- policy section
- chunk index

The current retrieval uses a local fallback scorer because ChromaDB cannot be installed cleanly on this Windows/Python 3.13 environment without native build tools.

The fallback retrieval still follows the same concept:

- tokenize the user query
- score product and policy chunks
- rank the most relevant chunks
- return the top matches with metadata

ChromaDB support is present in the code and can be enabled later in an environment where its native dependency installs correctly.

## 8. Deterministic Order Tools

Order actions are not handled by free-form AI generation.

This is one of the most important parts of the project.

For example, if a user says:

```text
Cancel order #9982 for maya@example.com
```

The assistant should not simply generate:

```text
Sure, I cancelled your order.
```

That would be unsafe unless the backend actually checked and updated the order.

Instead, we created deterministic tools:

- `track_order`
- `cancel_order`
- `request_refund`

Each tool uses strict schemas and backend business logic.

The backend checks:

- Does the order exist?
- Does the email match?
- What is the current order status?
- Is cancellation allowed?
- Is refund request allowed?

Only then does it return a result.

This gives us safe, database-backed responses.

## 9. Pydantic Schemas

Pydantic schemas are used throughout the project to keep inputs and outputs structured.

Important schemas include:

- `ChatRequest`
- `ChatResponse`
- `Citation`
- `RetrievedContext`
- `OrderActionRequest`
- `RefundRequest`
- `ToolCallRequest`
- `ToolCallResult`
- `GroundednessResult`

This is important because it prevents loose, inconsistent JSON shapes. The frontend and backend both know what fields to expect.

For an interviewer, this shows that the project is not just a prompt demo. It has typed API contracts and structured boundaries.

## 10. Interaction Logging

Every chat interaction is logged.

The logs include:

- user query
- selected route
- response text
- latency
- timestamp

For RAG answers, the system also logs retrieved context.

For tool actions, the system logs tool execution results.

This matters because AI systems need observability. If a response is wrong, we need to know:

- what the user asked
- which route was selected
- what context was retrieved
- what answer was generated
- what tool was called
- what result came back

This is the difference between a demo chatbot and an inspectable assistant system.

## 11. Groundedness Scoring

Groundedness scoring checks whether a RAG answer is supported by the retrieved context.

The current implementation compares meaningful answer tokens against retrieved context tokens and produces:

- score
- explanation

Example:

```text
87 supported tokens, 7 unsupported tokens.
```

This is not a perfect production evaluator, but it demonstrates the quality-scoring concept.

It shows that the project is thinking beyond just generating answers. It also measures whether those answers are supported.

For an interview, this connects directly to AI evaluation and quality monitoring.

## 12. Developer Console

The Developer Console is a separate frontend tab that shows what happened behind the scenes.

It displays:

- selected route
- citations
- retrieved context
- tool JSON
- deterministic tool result
- groundedness score
- raw backend response

The purpose of the Developer Console is transparency.

A normal user only needs the final answer. But an engineer, interviewer, or evaluator needs to see how the answer was produced.

For example:

- If the route is `rag`, the console shows which product or policy chunks were retrieved.
- If the route is `tool`, the console shows the extracted tool JSON and backend result.
- If the answer has citations, the console shows the exact source labels.
- If the answer has a groundedness score, the console shows the score and explanation.

This makes the project easier to debug and easier to explain.

It also proves that the assistant is not just generating text blindly.

## 13. Frontend

The frontend is a Streamlit app with two tabs:

1. ShopGuard AI
   - Customer-facing chat interface.
   - Shows structured product cards, policy sections, citations, and order results.

2. Developer Console
   - Technical inspection view.
   - Shows route, retrieval context, citations, tool payloads, and groundedness.

The frontend calls the backend `/api/chat` endpoint.

It also validates responses using the backend Pydantic schemas, which keeps the UI aligned with the API contract.

## 14. Tests

The project includes tests for the core behavior.

Test categories:

- API tests
- retrieval tests
- order business-rule tests
- safe unknown-answer tests

The tests verify:

- routes are registered
- product and policy chunks are created
- retrieval finds product and policy context
- unknown questions do not hallucinate
- order tracking works
- invalid email/order combinations fail safely
- cancellation rules are enforced
- refund request rules are enforced
- tool execution logs are created

This helps show that the project is maintainable and not just manually tested.

## 15. How To Explain It In An Interview

A good short explanation:

```text
ShopGuard AI is a grounded e-commerce assistant built with FastAPI, Streamlit, SQLModel, and Pydantic. It separates flexible knowledge questions from strict transaction actions. Product and policy questions use retrieval-augmented generation with citations, while order actions use deterministic backend tools so the AI cannot falsely claim that an order was cancelled or refunded. The project also includes interaction logging, groundedness scoring, and a Developer Console to make the system transparent and debuggable.
```

A slightly deeper explanation:

```text
The key design decision was to route different query types differently. For product and policy questions, we retrieve the relevant product or policy chunks and answer from that context. For order actions, we extract structured parameters like order ID and email, validate them with Pydantic, and execute backend logic against the database. The frontend shows both the customer answer and a developer-facing inspection panel so an interviewer can see the route, retrieved context, citations, tool payloads, and deterministic result.
```

## 16. Why This Is Above A Basic Chatbot

This project is stronger than a basic chatbot because it includes:

- typed schemas
- backend API boundaries
- grounded retrieval
- citations
- deterministic order tools
- database-backed order actions
- interaction logging
- groundedness scoring
- frontend developer console
- tests
- clean phase-based implementation

A basic chatbot only returns text.

ShopGuard AI shows how the answer was produced and uses deterministic backend logic where correctness matters.

## 17. Current Limitations

The project is still a demo, so there are known limitations:

- It uses mock Shopify-style data, not a real Shopify API.
- The local demo uses SQLite, though the project is configured for PostgreSQL.
- ChromaDB code exists, but this environment uses local retrieval fallback because Chroma's native dependency does not install cleanly on Windows/Python 3.13.
- The groundedness metric is simple and would need a stronger evaluator for production.
- There is no authentication yet.

These are acceptable for the current project scope because the goal is to demonstrate architecture, grounding, tool safety, observability, and a working end-to-end demo.

## 18. Best Demo Flow

Use this order when presenting:

1. Open the Streamlit frontend.
2. Ask:

```text
tell me about your products
```

Show the structured product cards and citations.

3. Ask:

```text
what is your return policy?
```

Show policy answer and source citations.

4. Ask:

```text
Track order #9982 for maya@example.com
```

Show that the response comes from deterministic tool execution.

5. Open Developer Console.

Show:

- route
- retrieved context
- citations
- tool JSON
- deterministic result
- groundedness score

6. Explain that the system is built to be inspectable and safe, not just conversational.

