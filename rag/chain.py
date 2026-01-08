from langchain_core.messages import SystemMessage, HumanMessage  # 메시지 타입
from vectorstore.retriever import retrieve_docs  # 검색 함수
from rag.prompt import build_prompt  # 프롬프트 생성
from app.config import NO_CONTEXT_RESPONSE

# Chunk Attribution 포함 RAG Chain
def run_rag_chain(llm, vectordb, user_query: str):
    # 1. 문서 검색
    docs = retrieve_docs(vectordb, user_query)

    # 검색 실패 시 fallback
    if not docs:
        return {
            "answer": NO_CONTEXT_RESPONSE,
            "attribution": []
        }
    
     # 2. Re-ranking 단계
    reranked = rerank_docs(docs)

    # 3. context 구성
    context = "\n\n".join([doc.page_content for doc in reranked]) # docs -> reranked

    # 4. Attribution 메타데이터 구성
    attribution = [
        {
            "doc_id": doc.metadata.get("doc_id"),
            "score": score
        }
        for doc, score in reranked
    ]

    # 프롬프트 생성
    prompt = build_prompt(context, user_query)

    # LLM 호출
    response = llm.invoke([
        SystemMessage(content=
            "당신은 대학교 행정 업무를 지원하는 전문적인 AI 어시스턴트입니다."
            "답변 끝에 불필요한 이모지나 사족을 달지 마세요."
            "반드시 사실 기반으로만 답변하십시오."
            "반드시 격식 있고 정중한 존댓말(하십시오체)을 사용해야 합니다."
        ), # 시스템 프롬프트 약간 구체화
        HumanMessage(content=prompt)
    ],
      # 🔥 핵심 파라미터
        top_p=0.9,          # 누적 확률 기반 샘플링
        top_k=60,           # 상한 제한
        temperature=0.3     # 안정성 중시
    )
    
    return response.content

# 1. Retrieval → Re-ranking → LLM 연결 로직

# 개념: Retrieval 단계에서 가져온 문서를 Re-ranking(재정렬)하여 LLM에 전달. 
# Re-ranking은 BM25, Cross-Encoder, 또는 Scoring 모델을 활용. -> 현재는 score 기반 정렬 구조 
# 수정 방향:
# chain.py에서 retrieve_docs 호출 후, Re-ranking 단계 추가.
# Re-ranking 점수를 기반으로 문서 정렬 후 상위 문서만 LLM에 전달.

def rerank_docs(docs_with_scores, top_n: int = 8):
    # score 기준 오름차순 정렬 (FAISS L2 → 낮을수록 유사)
    sorted_docs = sorted(
        docs_with_scores,
        key=lambda x: x[1]  # score 기준
    )

    # 상위 top_n개 선택
    return sorted_docs[:top_n]

# 2. Chunk Attribution 기능 구현
