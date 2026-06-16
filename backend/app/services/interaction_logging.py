from time import perf_counter

from sqlmodel import Session, select

from app.models.log import EvaluationLog, InteractionLog, RetrievedContextLog
from app.schemas.chat import ChatResponse, ChatRoute, RetrievedContext
from app.services.evaluation import score_groundedness


def create_interaction_start(session: Session, user_query: str, route: ChatRoute) -> InteractionLog:
    interaction = InteractionLog(user_query=user_query, selected_route=route.value)
    session.add(interaction)
    session.commit()
    session.refresh(interaction)
    return interaction


def finish_interaction(
    session: Session,
    interaction: InteractionLog,
    response: ChatResponse,
    started_at: float,
) -> None:
    interaction.selected_route = response.route.value
    interaction.response_text = response.answer
    interaction.latency_ms = int((perf_counter() - started_at) * 1000)
    session.add(interaction)

    if response.route == ChatRoute.rag:
        for context in response.retrieved_context:
            session.add(_build_context_log(interaction.id, context))

        groundedness = score_groundedness(
            answer=response.answer,
            contexts=[context.content for context in response.retrieved_context],
        )
        session.add(
            EvaluationLog(
                interaction_log_id=interaction.id,
                metric_name=groundedness.metric_name,
                score=groundedness.score,
                explanation=groundedness.explanation,
            )
        )

    session.commit()


def log_completed_interaction(
    session: Session,
    user_query: str,
    response: ChatResponse,
    started_at: float,
) -> InteractionLog:
    interaction = create_interaction_start(session=session, user_query=user_query, route=response.route)
    finish_interaction(session=session, interaction=interaction, response=response, started_at=started_at)
    return interaction


def evaluate_saved_rag_interactions(session: Session) -> int:
    interactions = session.exec(
        select(InteractionLog).where(InteractionLog.selected_route == ChatRoute.rag.value)
    ).all()
    created_count = 0

    for interaction in interactions:
        existing = session.exec(
            select(EvaluationLog).where(
                EvaluationLog.interaction_log_id == interaction.id,
                EvaluationLog.metric_name == "groundedness",
            )
        ).first()
        if existing is not None or not interaction.response_text:
            continue

        contexts = session.exec(
            select(RetrievedContextLog).where(RetrievedContextLog.interaction_log_id == interaction.id)
        ).all()
        groundedness = score_groundedness(
            answer=interaction.response_text,
            contexts=[context.content_preview for context in contexts],
        )
        session.add(
            EvaluationLog(
                interaction_log_id=interaction.id,
                metric_name=groundedness.metric_name,
                score=groundedness.score,
                explanation=groundedness.explanation,
            )
        )
        created_count += 1

    session.commit()
    return created_count


def _build_context_log(interaction_log_id: int, context: RetrievedContext) -> RetrievedContextLog:
    return RetrievedContextLog(
        interaction_log_id=interaction_log_id,
        source_type=context.source_type.value,
        source_file=context.source_file,
        source_id=context.source_id,
        content_preview=context.content,
        context_metadata={
            "chunk_id": context.chunk_id,
            "title": context.title,
            "section": context.section,
            "distance": context.distance,
        },
    )

