from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evaluation import GroundednessResult
from app.schemas.knowledge import SourceType
from app.schemas.order import ToolCallRequest, ToolCallResult


class ChatRoute(str, Enum):
    rag = "rag"
    unknown = "unknown"
    tool = "tool"


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=5)


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    source_file: str
    source_id: str
    label: str


class RetrievedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    content: str
    source_type: SourceType
    source_file: str
    source_id: str
    title: str | None = None
    section: str | None = None
    distance: float | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: ChatRoute
    answer: str
    citations: list[Citation] = []
    retrieved_context: list[RetrievedContext] = []
    tool_call: ToolCallRequest | None = None
    tool_result: ToolCallResult | None = None
    evaluation: GroundednessResult | None = None
