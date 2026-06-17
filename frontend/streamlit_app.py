from __future__ import annotations

import os
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.chat import ChatRequest, ChatResponse

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


def normalize_api_base_url(raw_url: str | None) -> str:
    url = (raw_url or DEFAULT_API_BASE_URL).strip()
    markdown_match = re.match(r"^\[(https?://[^\]]+)\]\([^)]+\)$", url)
    if markdown_match:
        url = markdown_match.group(1)

    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        return DEFAULT_API_BASE_URL

    return url


API_BASE_URL = normalize_api_base_url(os.getenv("SHOPGUARD_API_BASE_URL"))


def call_chat(message: str, top_k: int) -> dict[str, Any]:
    request_payload = ChatRequest(message=message, top_k=top_k)
    response = requests.post(
        f"{API_BASE_URL}/api/chat",
        json=request_payload.model_dump(mode="json"),
        timeout=45,
    )
    response.raise_for_status()
    return ChatResponse.model_validate(response.json()).model_dump(mode="json")


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_response", None)
    st.session_state.setdefault("top_k", 3)


def render_developer_console(response: dict[str, Any] | None) -> None:
    st.header("Developer Console")
    if not response:
        st.info("Send a message to inspect the route, context, citations, and tool output.")
        return

    route = response.get("route", "unknown")
    evaluation = response.get("evaluation")
    tool_result = response.get("tool_result") or {}

    metric_columns = st.columns(3)
    metric_columns[0].metric("Route", route)
    metric_columns[1].metric("Citations", len(response.get("citations") or []))
    metric_columns[2].metric(
        "Groundedness",
        evaluation.get("score") if evaluation else "N/A",
    )

    if tool_result:
        st.success(f"Tool result: {tool_result.get('result_code', 'completed')}")

    citations = response.get("citations") or []
    with st.expander("Citations", expanded=True):
        if citations:
            for citation in citations:
                st.caption(citation.get("label", "Source"))
        else:
            st.caption("No citations returned.")

    contexts = response.get("retrieved_context") or []
    with st.expander("Retrieved Context", expanded=bool(contexts)):
        if contexts:
            for index, context in enumerate(contexts, start=1):
                st.markdown(f"**{index}. {context.get('source_file')} / {context.get('source_id')}**")
                st.caption(f"Distance: {context.get('distance')}")
                st.code(context.get("content", ""), language="text")
        else:
            st.caption("No retrieved context returned.")

    with st.expander("Tool JSON", expanded=bool(response.get("tool_call"))):
        st.json(response.get("tool_call") or {})

    with st.expander("Deterministic Result", expanded=bool(response.get("tool_result"))):
        st.json(response.get("tool_result") or {})

    with st.expander("Groundedness", expanded=bool(evaluation)):
        if evaluation:
            st.metric("Score", evaluation.get("score"))
            st.caption(evaluation.get("explanation"))
        else:
            st.caption("No groundedness score returned for this response.")

    with st.expander("Raw Response"):
        st.json(response)


def render_chat_panel() -> None:
    st.header("ShopGuard AI")

    st.caption("Ask grounded product and policy questions, or run deterministic order actions.")

    top_k = st.slider("Context results", min_value=1, max_value=5, value=st.session_state.top_k)
    st.session_state.top_k = top_k

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_response = None
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("response"):
                render_assistant_answer(message["response"], message["content"])
            else:
                st.write(message["content"])

    prompt = st.chat_input("Ask about products, policies, or an order")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        response = call_chat(prompt, top_k=top_k)
        answer = response.get("answer", "No answer returned.")
        st.session_state.last_response = response
    except requests.RequestException as exc:
        answer = f"Backend request failed: {exc}"
        st.session_state.last_response = None

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "response": st.session_state.last_response,
        }
    )
    st.rerun()


def render_assistant_answer(response: dict[str, Any] | None, fallback_answer: str) -> None:
    if not response:
        st.write(fallback_answer)
        return

    route = response.get("route")
    if route == "tool" and response.get("tool_result"):
        result = response["tool_result"]
        st.markdown(f"**{result.get('message', fallback_answer)}**")
        detail_columns = st.columns(3)
        detail_columns[0].metric("Order", result.get("order_id") or "N/A")
        detail_columns[1].metric("Status", result.get("order_status") or "N/A")
        detail_columns[2].metric("Result", result.get("result_code") or "N/A")
        if result.get("tracking_number"):
            st.caption(f"Tracking: {result['tracking_number']}")
        return

    if route == "rag":
        render_structured_rag_answer(response, fallback_answer)
        return

    st.write(response.get("answer", fallback_answer))

    citations = response.get("citations") or []
    if citations:
        st.markdown("**Sources**")
        for citation in citations:
            st.caption(citation.get("label", "Source"))


def render_structured_rag_answer(response: dict[str, Any], fallback_answer: str) -> None:
    contexts = response.get("retrieved_context") or []
    product_contexts = [context for context in contexts if context.get("source_type") == "product"]
    policy_contexts = [context for context in contexts if context.get("source_type") == "policy"]
    answer = response.get("answer") or fallback_answer
    direct_answer = extract_direct_answer(answer)

    if not contexts:
        st.write(answer)
        return

    if direct_answer:
        st.markdown(
            f"""
            <div class="sg-answer-card">
              <div class="sg-answer-label">Answer</div>
              <div class="sg-answer-copy">{escape(direct_answer)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if product_contexts:
        st.markdown("**Products**")
        for context in product_contexts:
            render_product_result(context)

    if policy_contexts:
        st.markdown("**Store Policies**")
        for context in policy_contexts:
            render_policy_result(context)

    citations = response.get("citations") or []
    if citations:
        st.markdown("**Sources**")
        source_text = "  \n".join(f"- {citation.get('label', 'Source')}" for citation in citations)
        st.markdown(source_text)


def render_product_result(context: dict[str, Any]) -> None:
    parsed = parse_product_context(context.get("content", ""))
    title = parsed.get("Product") or context.get("title") or context.get("source_id")
    sku = parsed.get("SKU") or context.get("source_id")
    category = parsed.get("Category", "Product")
    price = parsed.get("Base price", "N/A")
    description = parsed.get("Description", "")
    variants = parsed.get("Variants", [])

    st.markdown(
        f"""
        <div class="sg-result-card">
          <div class="sg-card-topline">{category} &middot; {sku}</div>
          <div class="sg-card-title">{title}</div>
          <div class="sg-card-price">{price}</div>
          <div class="sg-card-copy">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if variants:
        st.markdown("Available variants:")
        for variant in variants:
            st.markdown(f"- {variant}")


def render_policy_result(context: dict[str, Any]) -> None:
    content = context.get("content", "")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    section = context.get("section") or context.get("source_id") or "Policy"
    body = " ".join(lines[1:] if lines and lines[0].lower() == str(section).lower() else lines)

    st.markdown(
        f"""
        <div class="sg-policy-card">
          <div class="sg-card-topline">Policy &middot; {context.get('source_file')}</div>
          <div class="sg-card-title">{section}</div>
          <div class="sg-card-copy">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_product_context(content: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {"Variants": []}
    current_section = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "Variants:":
            current_section = "Variants"
            continue
        if current_section == "Variants":
            parsed["Variants"].append(line)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()

    return parsed


def extract_direct_answer(answer: str) -> str:
    if answer.startswith(("Product information:", "Policy information:")):
        return ""
    for marker in ["\n\nProduct information:", "\n\nPolicy information:"]:
        if marker in answer:
            return answer.split(marker, 1)[0].strip()
    return answer.strip()


def main() -> None:
    st.set_page_config(
        page_title="ShopGuard AI",
        page_icon="SG",
        layout="wide",
    )
    init_state()

    st.markdown(
        """
        <style>
        .stApp { background: #f8fafc; }
        .block-container { padding-top: 1.25rem; max-width: 1120px; }
        h1, h2, h3 { letter-spacing: 0; color: #111827; }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 0.85rem;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 1px solid #e5e7eb;
        }
        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-bottom: 0;
            border-radius: 8px 8px 0 0;
            padding: 0.65rem 1rem;
        }
        .sg-result-card, .sg-policy-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.55rem 0 0.85rem 0;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }
        .sg-policy-card { box-shadow: 0 6px 18px rgba(15, 23, 42, 0.045); }
        .sg-card-topline {
            color: #64748b;
            font-size: 0.8rem;
            margin-bottom: 0.3rem;
        }
        .sg-card-title {
            color: #0f172a;
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .sg-card-price {
            color: #0f766e;
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }
        .sg-card-copy {
            color: #334155;
            line-height: 1.55;
        }
        .sg-answer-card {
            background: #ffffff;
            border: 1px solid #d1fae5;
            border-left: 4px solid #0f766e;
            border-radius: 8px;
            padding: 0.95rem 1.05rem;
            margin: 0.55rem 0 0.9rem 0;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        }
        .sg-answer-label {
            color: #0f766e;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
        }
        .sg-answer-copy {
            color: #0f172a;
            line-height: 1.55;
        }
        code { white-space: pre-wrap !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("ShopGuard AI")
    st.caption("Grounded storefront assistant with transparent retrieval and deterministic order tools.")

    chat_tab, console_tab = st.tabs(["ShopGuard AI", "Developer Console"])
    with chat_tab:
        render_chat_panel()
    with console_tab:
        render_developer_console(st.session_state.last_response)


if __name__ == "__main__":
    main()
