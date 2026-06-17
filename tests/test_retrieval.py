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


def test_policy_only_question_returns_policy_context_only(test_session) -> None:
    response = answer_chat("what is refund policy", session=test_session)
    product_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "product"
    ]
    policy_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "policy"
    ]

    assert response.route == "rag"
    assert product_sources == []
    assert policy_sources == ["refunds"]
    assert response.answer.startswith("Refunds: Refunds are reviewed")


def test_mixed_product_and_policy_question_keeps_both_contexts(test_session) -> None:
    response = answer_chat(
        "Does the leather jacket come in brown and what is the return policy?",
        session=test_session,
    )
    source_ids = {context.source_id for context in response.retrieved_context}

    assert response.route == "rag"
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


def test_color_question_gets_direct_grounded_answer(test_session) -> None:
    response = answer_chat("does the leather jacket comes in brown color", session=test_session)

    assert response.route == "rag"
    assert response.answer.startswith("Yes. Aster Leather Jacket is available in Brown / M")
    assert response.citations[0].source_id == "SG-JACKET-LEATHER"


def test_wallet_recommendation_routes_to_wallet_product(test_session) -> None:
    response = answer_chat("give me suggestion for some wallets", session=test_session)
    product_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "product"
    ]
    policy_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "policy"
    ]

    assert response.route == "rag"
    assert product_sources == ["SG-WALLET-SLIM"]
    assert policy_sources == []
    assert response.answer.startswith("Yes. I found Nolan Slim Wallet.")


def test_wallet_availability_typo_routes_to_wallet_product(test_session) -> None:
    response = answer_chat("is there any wallet avbailable", session=test_session)
    product_sources = [
        context.source_id
        for context in response.retrieved_context
        if context.source_type == "product"
    ]

    assert response.route == "rag"
    assert product_sources == ["SG-WALLET-SLIM"]
    assert response.answer.startswith("Yes. I found Nolan Slim Wallet.")


def test_unknown_question_uses_safe_answer(test_session) -> None:
    response = answer_chat("Who won the world cup?", session=test_session)

    assert response.route == "unknown"
    assert response.answer == "I don't know from the available store data."
    assert response.citations == []
