from kure_search import search


class DeterministicModel:
    """Offline stand-in for the encoder's public retrieval interface."""

    def encode_query(self, query):
        return query

    def similarity(self, query_embedding, document_embeddings):
        assert query_embedding == "궁궐을 지은 왕은 누구야?"
        assert document_embeddings == ["doc-0", "doc-1", "doc-2"]
        return [[0.25, 0.90, 0.50]]


def test_search_returns_documents_in_descending_score_order():
    """A ranking bug that leaves model scores unsorted must be visible."""
    results = search(
        "궁궐을 지은 왕은 누구야?",
        k=2,
        model=DeterministicModel(),
        documents=["세종은 한글을 창제했다.", "경복궁은 조선의 궁궐이다.", "김치는 한국의 음식이다."],
        doc_embeddings=["doc-0", "doc-1", "doc-2"],
    )

    assert results == [
        (1, 0.90, "경복궁은 조선의 궁궐이다."),
        (2, 0.50, "김치는 한국의 음식이다."),
    ]


def test_search_limits_results_when_k_exceeds_document_count():
    """An oversized k must not cause an index error or duplicate results."""
    results = search(
        "궁궐을 지은 왕은 누구야?",
        k=10,
        model=DeterministicModel(),
        documents=["세종은 한글을 창제했다.", "경복궁은 조선의 궁궐이다.", "김치는 한국의 음식이다."],
        doc_embeddings=["doc-0", "doc-1", "doc-2"],
    )

    assert [index for index, _, _ in results] == [1, 2, 0]
