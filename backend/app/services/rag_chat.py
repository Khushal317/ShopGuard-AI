import json
import re
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from sqlmodel import Session

from app.models.log import InteractionLog
from app.schemas.chat import ChatResponse, ChatRoute, Citation, RetrievedContext
from app.schemas.knowledge import KnowledgeSearchResult, SourceType
from app.services.interaction_logging import create_interaction_start, finish_interaction, log_completed_interaction
from app.services.knowledge_ingestion import search_knowledge_base
from app.services.order_tool_router import detect_order_tool, execute_tool_call

KNOWLEDGE_PATTERN = re.compile(
    r"\b(product|price|stock|variant|size|color|jacket|sneaker|tote|bag|shipping|return policy|refund policy|policy|delivery)\b",
    re.IGNORECASE,
)


def answer_chat(message: str, top_k: int = 3, session: Session | None = None) -> ChatResponse:
    started_at = perf_counter()
    if session is None:
        from app.db.session import get_session

        session_generator = get_session()
        owned_session = next(session_generator)
        try:
            return _answer_chat_with_session(message=message, top_k=top_k, session=owned_session, started_at=started_at)
        finally:
            owned_session.close()

    return _answer_chat_with_session(message=message, top_k=top_k, session=session, started_at=started_at)


def _answer_chat_with_session(message: str, top_k: int, session: Session, started_at: float) -> ChatResponse:
    tool_call = detect_order_tool(message)
    if tool_call is not None and not KNOWLEDGE_PATTERN.search(message):
        interaction = create_interaction_start(session=session, user_query=message, route=ChatRoute.tool)
        tool_result = execute_tool_call(
            session=session,
            tool_call=tool_call,
            interaction_log_id=interaction.id,
        )
        response = ChatResponse(
            route=ChatRoute.tool,
            answer=tool_result.message,
            tool_call=tool_call,
            tool_result=tool_result,
        )
        finish_interaction(session=session, interaction=interaction, response=response, started_at=started_at)
        return response

    if not KNOWLEDGE_PATTERN.search(message):
        response = ChatResponse(
            route=ChatRoute.unknown,
            answer="I don't know from the available store data.",
        )
        log_completed_interaction(session=session, user_query=message, response=response, started_at=started_at)
        return response

    results = search_knowledge_base(query=message, limit=top_k)
    if not results:
        response = ChatResponse(
            route=ChatRoute.unknown,
            answer="I don't know from the available store data.",
        )
        log_completed_interaction(session=session, user_query=message, response=response, started_at=started_at)
        return response

    contexts = [_to_retrieved_context(result) for result in results]
    citations = [_to_citation(result) for result in results]

    response = ChatResponse(
        route=ChatRoute.rag,
        answer=_generate_grounded_answer(message=message, results=results),
        citations=_dedupe_citations(citations),
        retrieved_context=contexts,
    )
    log_completed_interaction(session=session, user_query=message, response=response, started_at=started_at)
    return response


def _generate_grounded_answer(message: str, results: list[KnowledgeSearchResult]) -> str:
    settings = get_settings()
    if settings.groq_api_key:
        groq_answer = _generate_with_groq(message=message, results=results)
        if groq_answer:
            return groq_answer

    return _build_grounded_answer(results)


def _generate_with_groq(message: str, results: list[KnowledgeSearchResult]) -> str | None:
    settings = get_settings()
    context = "\n\n".join(
        f"[{_citation_label(result)}]\n{result.content}"
        for result in results
    )
    payload = {
        "model": settings.groq_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are ShopGuard AI. Answer only using the provided store context. "
                    "If the context is insufficient, say: I don't know from the available store data. "
                    "Include citation labels exactly as they appear in the context."
                ),
            },
            {
                "role": "user",
                "content": f"Store context:\n{context}\n\nCustomer question:\n{message}",
            },
        ],
        "temperature": 0,
    }
    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    choices = body.get("choices", [])
    if not choices:
        return None

    content = choices[0].get("message", {}).get("content")
    return content.strip() if isinstance(content, str) and content.strip() else None


def _build_grounded_answer(results: list[KnowledgeSearchResult]) -> str:
    product_lines: list[str] = []
    policy_lines: list[str] = []

    for result in results:
        label = _citation_label(result)
        if result.metadata.source_type == SourceType.product:
            product_lines.append(f"{_compact_content(result.content)} [{label}]")
        elif result.metadata.source_type == SourceType.policy:
            policy_lines.append(f"{_compact_content(result.content)} [{label}]")

    answer_parts: list[str] = []
    if product_lines:
        answer_parts.append("Product information: " + " ".join(product_lines))
    if policy_lines:
        answer_parts.append("Policy information: " + " ".join(policy_lines))

    if not answer_parts:
        return "I don't know from the available store data."

    return "\n\n".join(answer_parts)


def _compact_content(content: str) -> str:
    text = " ".join(line.strip() for line in content.splitlines() if line.strip())
    return text[:700]


def _to_retrieved_context(result: KnowledgeSearchResult) -> RetrievedContext:
    return RetrievedContext(
        chunk_id=result.chunk_id,
        content=result.content,
        source_type=result.metadata.source_type,
        source_file=result.metadata.source_file,
        source_id=result.metadata.source_id,
        title=result.metadata.title,
        section=result.metadata.section,
        distance=result.distance,
    )


def _to_citation(result: KnowledgeSearchResult) -> Citation:
    return Citation(
        source_type=result.metadata.source_type,
        source_file=result.metadata.source_file,
        source_id=result.metadata.source_id,
        label=_citation_label(result),
    )


def _citation_label(result: KnowledgeSearchResult) -> str:
    if result.metadata.source_type == SourceType.product:
        return f"Source: {result.metadata.source_file}, SKU {result.metadata.source_id}"

    return f"Source: {result.metadata.source_file}, {result.metadata.section}"


def _dedupe_citations(citations: list[Citation]) -> list[Citation]:
    deduped: list[Citation] = []
    seen: set[tuple[str, str, str]] = set()

    for citation in citations:
        key = (citation.source_type.value, citation.source_file, citation.source_id)
        if key not in seen:
            seen.add(key)
            deduped.append(citation)

    return deduped
