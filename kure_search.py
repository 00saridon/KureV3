"""KURE MultiVectorEncoder를 이용한 작은 문서 검색 유틸리티."""


def search(query, k, model, documents, doc_embeddings):
    """질문과 미리 생성한 문서 임베딩에서 점수 순으로 상위 k개를 찾는다."""
    if k < 1:
        raise ValueError("k는 1 이상이어야 합니다.")
    if len(documents) != len(doc_embeddings):
        raise ValueError("documents와 doc_embeddings의 개수가 같아야 합니다.")

    query_embedding = model.encode_query(query)
    scores = model.similarity(query_embedding, doc_embeddings)[0]
    ranked = sorted(
        enumerate(scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    return [
        (index, float(score), documents[index])
        for index, score in ranked[:k]
    ]
