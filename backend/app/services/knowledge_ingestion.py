import json
import math
import re
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.schemas.knowledge import (
    IngestionSummary,
    KnowledgeChunk,
    KnowledgeChunkMetadata,
    KnowledgeSearchResult,
    SourceType,
)
from app.schemas.product import ProductSeed
from app.services.local_embeddings import LocalHashEmbeddingFunction

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data" / "mock_shopify"


def build_product_chunks(products_path: Path = DATA_DIR / "products.json") -> list[KnowledgeChunk]:
    raw_products = json.loads(products_path.read_text(encoding="utf-8"))
    chunks: list[KnowledgeChunk] = []

    for product_index, raw_product in enumerate(raw_products):
        product = ProductSeed.model_validate(raw_product)
        variant_lines = [
            f"{variant.color} / {variant.size}: sku {variant.variant_sku}, stock {variant.stock}, price {variant.price} {product.currency}"
            for variant in product.variants
        ]
        content = "\n".join(
            [
                f"Product: {product.title}",
                f"SKU: {product.sku}",
                f"Category: {product.category}",
                f"Description: {product.description}",
                f"Base price: {product.price} {product.currency}",
                "Variants:",
                *variant_lines,
            ]
        )

        chunks.append(
            KnowledgeChunk(
                chunk_id=f"product-{product.sku.lower()}",
                content=content,
                metadata=KnowledgeChunkMetadata(
                    source_type=SourceType.product,
                    source_file=products_path.name,
                    source_id=product.sku,
                    chunk_index=product_index,
                    sku=product.sku,
                    title=product.title,
                ),
            )
        )

    return chunks


def build_policy_chunks(policies_path: Path = DATA_DIR / "policies.md") -> list[KnowledgeChunk]:
    policy_text = policies_path.read_text(encoding="utf-8")
    sections = re.findall(r"^##\s+(.+?)\n\n(.*?)(?=^##\s+|\Z)", policy_text, flags=re.MULTILINE | re.DOTALL)
    chunks: list[KnowledgeChunk] = []

    for section_index, (section_title, section_body) in enumerate(sections):
        content = f"{section_title.strip()}\n\n{section_body.strip()}"
        source_id = section_title.strip().lower().replace(" ", "_")
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"policy-{source_id}",
                content=content,
                metadata=KnowledgeChunkMetadata(
                    source_type=SourceType.policy,
                    source_file=policies_path.name,
                    source_id=source_id,
                    chunk_index=section_index,
                    section=section_title.strip(),
                ),
            )
        )

    return chunks


def build_knowledge_chunks() -> list[KnowledgeChunk]:
    return [*build_product_chunks(), *build_policy_chunks()]


def get_chroma_collection(rebuild: bool = False):
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "ChromaDB is not installed. Install backend requirements before running ingestion."
        ) from exc

    settings = get_settings()
    persist_dir = ROOT_DIR / settings.chroma_persist_dir

    if rebuild and persist_dir.exists():
        shutil.rmtree(persist_dir)

    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=LocalHashEmbeddingFunction(),
        metadata={"description": "ShopGuard AI product and policy knowledge base"},
    )


def ingest_knowledge_base(rebuild: bool = True) -> IngestionSummary:
    settings = get_settings()
    chunks = build_knowledge_chunks()
    product_chunks = [chunk for chunk in chunks if chunk.metadata.source_type == SourceType.product]
    policy_chunks = [chunk for chunk in chunks if chunk.metadata.source_type == SourceType.policy]

    collection = get_chroma_collection(rebuild=rebuild)
    collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.content for chunk in chunks],
        metadatas=[chunk.chroma_metadata() for chunk in chunks],
    )

    return IngestionSummary(
        collection_name=settings.chroma_collection_name,
        persist_dir=settings.chroma_persist_dir,
        product_chunks=len(product_chunks),
        policy_chunks=len(policy_chunks),
        total_chunks=len(chunks),
    )


def search_knowledge_base(query: str, limit: int = 3) -> list[KnowledgeSearchResult]:
    try:
        collection = get_chroma_collection(rebuild=False)
    except RuntimeError:
        return search_local_knowledge_base(query=query, limit=limit)

    response = collection.query(query_texts=[query], n_results=limit)

    ids = response.get("ids", [[]])[0]
    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0] if response.get("distances") else [None] * len(ids)

    return [
        KnowledgeSearchResult(
            chunk_id=chunk_id,
            content=document,
            metadata=KnowledgeChunkMetadata.model_validate(metadata),
            distance=distance,
        )
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances, strict=True)
    ]


def search_local_knowledge_base(query: str, limit: int = 3) -> list[KnowledgeSearchResult]:
    embedding_function = LocalHashEmbeddingFunction()
    query_vector = embedding_function.embed_text(query)
    query_tokens = _tokenize_for_search(query)
    scored_chunks: list[tuple[float, KnowledgeChunk]] = []

    for chunk in build_knowledge_chunks():
        chunk_vector = embedding_function.embed_text(chunk.content)
        vector_similarity = sum(
            query_value * chunk_value for query_value, chunk_value in zip(query_vector, chunk_vector, strict=True)
        )
        metadata_text = " ".join(
            value
            for value in [chunk.metadata.title, chunk.metadata.section, chunk.metadata.source_id, chunk.metadata.sku]
            if value
        )
        metadata_tokens = _tokenize_for_search(metadata_text)
        lexical_similarity = _lexical_similarity(
            query_tokens,
            _tokenize_for_search(f"{chunk.content} {metadata_text}"),
        )
        metadata_boost = 0.4 if query_tokens.intersection(metadata_tokens) else 0.0
        scored_chunks.append((lexical_similarity + metadata_boost + (0.15 * vector_similarity), chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    return [
        KnowledgeSearchResult(
            chunk_id=chunk.chunk_id,
            content=chunk.content,
            metadata=chunk.metadata,
            distance=1.0 - max(-1.0, min(1.0, score)) if math.isfinite(score) else None,
        )
        for score, chunk in scored_chunks[:limit]
        if score > 0
    ]


def _tokenize_for_search(text: str) -> set[str]:
    stop_words = {"a", "an", "and", "are", "can", "does", "is", "it", "of", "the", "to", "what", "with"}
    tokens = {_normalize_token(token) for token in re.findall(r"[a-z0-9]+", text.lower())}
    tokens = tokens.difference(stop_words)
    normalized = set(tokens)
    for token in tokens:
        if token.endswith("s") and len(token) > 3:
            normalized.add(token[:-1])
    return normalized


def _normalize_token(token: str) -> str:
    typo_map = {
        "lether": "leather",
        "jaket": "jacket",
        "jackt": "jacket",
        "sneekers": "sneakers",
        "sneeker": "sneaker",
        "policie": "policy",
        "policys": "policies",
    }
    return typo_map.get(token, token)


def _lexical_similarity(query_tokens: set[str], content_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0

    matches = query_tokens.intersection(content_tokens)
    return len(matches) / len(query_tokens)
