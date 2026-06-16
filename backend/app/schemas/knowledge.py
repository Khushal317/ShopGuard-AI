from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    product = "product"
    policy = "policy"


class KnowledgeChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    source_file: str
    source_id: str
    chunk_index: int
    sku: str | None = None
    title: str | None = None
    section: str | None = None


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    content: str = Field(min_length=1)
    metadata: KnowledgeChunkMetadata

    def chroma_metadata(self) -> dict[str, str | int]:
        return self.metadata.model_dump(mode="json", exclude_none=True)


class IngestionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collection_name: str
    persist_dir: str
    product_chunks: int
    policy_chunks: int
    total_chunks: int


class KnowledgeSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    content: str
    metadata: KnowledgeChunkMetadata
    distance: float | None = None

