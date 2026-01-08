# faiss_index.py

import faiss  # FAISS 명시적 사용
import numpy as np  # 벡터 배열 처리

class FaissIndex:
    def __init__(self, dim: int):
        # L2 거리 기반 FAISS 인덱스 생성
        self.index = faiss.IndexFlatL2(dim)  # 정확도 중심 구조
        self.documents = []  # 문서 매핑 저장소

    def add(self, embeddings: np.ndarray, docs: list):
        # 벡터를 FAISS 인덱스에 추가
        self.index.add(embeddings)  # 벡터 삽입
        self.documents.extend(docs)  # 문서 순서 매핑

    def search(self, query_vector: np.ndarray, top_k: int):
        # FAISS 거리 기반 검색 수행
        distances, indices = self.index.search(query_vector, top_k)

        # 검색 결과를 (doc, score) 형태로 반환
        return [
            (self.documents[idx], distances[0][i])
            for i, idx in enumerate(indices[0])
        ]
