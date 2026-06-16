from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class InteractionLog(SQLModel, table=True):
    __tablename__ = "interaction_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_query: str
    selected_route: str | None = Field(default=None, index=True)
    response_text: str | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class RetrievedContextLog(SQLModel, table=True):
    __tablename__ = "retrieved_context_logs"

    id: int | None = Field(default=None, primary_key=True)
    interaction_log_id: int = Field(foreign_key="interaction_logs.id", index=True)
    source_type: str = Field(index=True)
    source_file: str
    source_id: str | None = None
    content_preview: str
    context_metadata: dict = Field(default_factory=dict, sa_column=Column("metadata", JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolExecutionLog(SQLModel, table=True):
    __tablename__ = "tool_execution_logs"

    id: int | None = Field(default=None, primary_key=True)
    interaction_log_id: int | None = Field(default=None, foreign_key="interaction_logs.id", index=True)
    tool_name: str = Field(index=True)
    tool_args: dict = Field(default_factory=dict, sa_column=Column(JSON))
    result_code: str
    result_payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationLog(SQLModel, table=True):
    __tablename__ = "evaluation_logs"

    id: int | None = Field(default=None, primary_key=True)
    interaction_log_id: int = Field(foreign_key="interaction_logs.id", index=True)
    metric_name: str
    score: float
    explanation: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
