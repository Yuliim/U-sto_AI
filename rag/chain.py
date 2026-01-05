from langchain_core.messages import SystemMessage, HumanMessage  # 메시지 타입
from vectorstore.retriever import retrieve_docs  # 검색 함수
from rag.prompt import build_prompt  # 프롬프트 생성

def run_rag_chain(llm, vectordb, user_query: str):
    # 문서 검색
    docs = retrieve_docs(vectordb, user_query)

    # 검색 실패 처리
    if not docs:
        return "관련 정보를 찾지 못했습니다."

    # 컨텍스트 결합
    context = "\n\n".join([doc.page_content for doc in docs])

    # 프롬프트 생성
    prompt = build_prompt(context, user_query)

    # LLM 호출
    response = llm.invoke([
        SystemMessage(content="도움이 되는 AI"),
        HumanMessage(content=prompt)
    ])

    return response.content
