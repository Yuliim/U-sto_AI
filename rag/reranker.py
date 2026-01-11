from sentence_transformers import CrossEncoder
from app.config import RERANK_DEBUG

_reranker_instance = None

def get_reranker(model_name: str):
    global _reranker_instance
    if _reranker_instance is None:
        if RERANK_DEBUG:
            print(f"[RERANKER] 모델 로딩: {model_name}")
        _reranker_instance = CrossEncoder(model_name)
    return _reranker_instance

class CrossEncoderReranker:
    def __init__(self, model_name: str):
        self.model = get_reranker(model_name)

        if RERANK_DEBUG:
            print("[RERANKER] 모델 로딩 완료")

    def rerank(self, query: str, docs: list, top_n: int):
        """
        Re-rank candidate documents for a query using a Cross-Encoder.

        Parameters
        ----------
        query : str
            사용자 질의 문자열
        docs : list
            (Document, retrieval_score) 형태의 리스트
        top_n : int
            반환할 상위 문서 개수

        Returns
        -------
        list
            Cross-Encoder 점수 기준으로 재정렬된 Document 리스트
        """
        if RERANK_DEBUG:
            print(f"[RERANKER] Re-ranking 시작 | 후보 수: {len(docs)}")

        pairs = [(query, doc.page_content) for doc, _ in docs]
        scores = self.model.predict(pairs)

        # 디버깅: 상위 5개 score 출력
        if RERANK_DEBUG: 
            for i, score in enumerate(scores[:5]):
                print(f"[RERANKER] score[{i}] = {score}")

        reranked = sorted(
            zip(docs, scores),
            key=lambda x: x[1],
            reverse=True
        )
        if RERANK_DEBUG:
            print("[RERANKER] Re-ranking 완료")
        return [doc for (doc, _), _ in reranked[:top_n]]
