# query embedding 생성
# similarity search
# top-k 문서 반환

# from app.config import RETRIEVER_TOP_K

# def retrieve_docs(vectordb, query: str, k: int = RETRIEVER_TOP_K):
#     # 사용자 질문을 기반으로 유사 문서 검색
#     return vectordb.similarity_search(
#         query=query,  # 검색 질의
#         k=k           # 상위 k개 반환
#     )

# retriever.py

def retrieve_docs(faiss_index, query_embedding, top_k: int):
    # FAISS 인덱스를 사용한 검색 수행
    return faiss_index.search(
        query_vector=query_embedding,
        top_k=top_k
    )
