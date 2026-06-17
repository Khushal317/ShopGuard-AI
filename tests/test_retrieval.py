from app.services.knowledge_ingestion import build_policy_chunks, build_product_chunks, search_local_knowledge_base
from app.services.rag_chat import answer_chat


def test_product_and_policy_chunks_have_citation_metadata() -> None:
    product_chunks = build_product_chunks()
    policy_chunks = build_policy_chunks()

    assert len(product_chunks) == 20
    assert len(policy_chunks) == 3
    assert product_chunks[0].metadata.source_file == "products.json"
    assert product_chunks[0].metadata.sku == "SG-JACKET-LEATHER"
    assert policy_chunks[0].metadata.source_file == "policies.md"
    assert policy_chunks[0].metadata.section == "Shipping"


def test_local_retrieval_finds_product_and_policy_context() -> None:
    results = search_local_knowledge_base(
        "Does the leather jacket come in brown and what is the return policy?",
        limit=3,
    )
    source_ids = {result.metadata.source_id for result in results}

    assert "SG-JACKET-LEATHER" in source_ids
    assert "returns" in source_ids


def test_exact_product_query_filters_unrelated_products(test_session) -> None:
    response = answer_chat("give me info about Aster Leather Jacket - Brown / M", session=test_session)
    product_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "product"
    ]

    assert product_sources == ["SG-JACKET-LEATHER"]


def test_typo_product_query_routes_to_relevant_product(test_session) -> None:
    response = answer_chat("give me info on lether jackets", session=test_session)
    product_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "product"
    ]

    assert response.route == "rag"
    assert product_sources == ["SG-JACKET-LEATHER"]


def test_unknown_question_uses_safe_answer(test_session) -> None:
    response = answer_chat("Who won the world cup?", session=test_session)

    assert response.route == "unknown"
    assert response.answer == "I don't know from the available store data."
    assert response.citations == []
