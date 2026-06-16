from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.chat import ChatRequest, ChatResponse

API_BASE_URL = os.getenv("SHOPGUARD_API_BASE_URL", "http://127.0.0.1:8000")


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
    st.subheader("Developer Console")
    if not response:
        st.info("Send a message to inspect the route, context, citations, and tool output.")
        return

    st.metric("Route", response.get("route", "unknown"))

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

    evaluation = response.get("evaluation")
    with st.expander("Groundedness", expanded=bool(evaluation)):
        if evaluation:
            st.metric("Score", evaluation.get("score"))
            st.caption(evaluation.get("explanation"))
        else:
            st.caption("No groundedness score returned for this response.")

    with st.expander("Raw Response"):
        st.json(response)


def render_chat_panel() -> None:
    st.subheader("ShopGuard AI")

    top_k = st.slider("Context results", min_value=1, max_value=5, value=st.session_state.top_k)
    st.session_state.top_k = top_k

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_response = None
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ask about products, policies, or an order")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    try:
        response = call_chat(prompt, top_k=top_k)
        answer = response.get("answer", "No answer returned.")
        st.session_state.last_response = response
    except requests.RequestException as exc:
        answer = f"Backend request failed: {exc}"
        st.session_state.last_response = None

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)


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
        .block-container { padding-top: 1.5rem; max-width: 1280px; }
        [data-testid="stMetric"] { background: #f7f8fa; border: 1px solid #e5e7eb; padding: 0.75rem; border-radius: 8px; }
        code { white-space: pre-wrap !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    chat_column, console_column = st.columns([1.15, 0.85], gap="large")
    with chat_column:
        render_chat_panel()
    with console_column:
        render_developer_console(st.session_state.last_response)


if __name__ == "__main__":
    main()
