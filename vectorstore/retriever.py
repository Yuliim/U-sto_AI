# query embedding 생성
# similarity search
# top-k 문서 반환

def retrieve_docs(vectordb, query: str, k: int = 3):
    # 사용자 질문을 기반으로 유사 문서 검색
    return vectordb.similarity_search(
        query=query,  # 검색 질의
        k=k           # 상위 k개 반환
    )
