from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InteractionLogRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    user_query: str
    selected_route: str | None
    response_text: str | None
    latency_ms: int | None
    created_at: datetime


class RetrievedContextLogRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    interaction_log_id: int
    source_type: str
    source_file: str
    source_id: str | None
    content_preview: str
    context_metadata: dict
    created_at: datetime


class ToolExecutionLogRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    interaction_log_id: int | None
    tool_name: str
    tool_args: dict
    result_code: str
    result_payload: dict
    created_at: datetime


class EvaluationLogRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    interaction_log_id: int
    metric_name: str
    score: float
    explanation: str | None
    created_at: datetime
