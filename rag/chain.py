from langchain_core.messages import SystemMessage, HumanMessage  # 메시지 타입
from vectorstore.retriever import retrieve_docs  # 검색 함수
from rag.prompt import build_prompt  # 프롬프트 생성
from app.config import NO_CONTEXT_RESPONSE

def run_rag_chain(llm, vectordb, user_query: str):
    # 문서 검색
    docs = retrieve_docs(vectordb, user_query)
    if not docs:
        return NO_CONTEXT_RESPONSE

    # 컨텍스트 결합
    context = "\n\n".join([doc.page_content for doc in docs])

    # 프롬프트 생성
    prompt = build_prompt(context, user_query)

    # LLM 호출
    response = llm.invoke([
        SystemMessage(content=
            "당신은 대학교 행정 업무를 지원하는 전문적인 AI 어시스턴트입니다."
            "답변 끝에 불필요한 이모지나 사족을 달지 마세요."
            "반드시 격식 있고 정중한 존댓말(하십시오체)을 사용해야 합니다."
        ), # 시스템 프롬프트 약간 구체화
        HumanMessage(content=prompt)
    ])

    return response.content
