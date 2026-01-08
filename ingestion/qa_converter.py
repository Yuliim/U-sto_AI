from langchain_openai import ChatOpenAI 
from langchain_core.messages import SystemMessage, HumanMessage  # 메시지 타입
from typing import Dict  # 타입 힌트
import json  # JSON 처리
import re    # 정규식 처리

def _extract_json(text: str) -> Dict:
    # LLM 응답에서 JSON만 추출하는 내부 함수
    try:
        return json.loads(text)  # 바로 파싱 시도
    except:
        # 마크다운 코드블록 제거
        text = text.replace("```json", "").replace("```", "")
        # 중괄호 {} 로 감싸진 부분만 정규식으로 추출
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())  # 추출된 JSON 파싱
    return {}  # 실패 시 빈 dict 반환

def convert_to_qa(item: Dict, llm: ChatOpenAI) -> Dict:
    # 단일 문서를 Q/A로 변환하고 메타데이터를 부착하는 함수

    # 입력 텍스트 구성 (챕터와 제목도 포함하여 AI에게 문맥 제공)
    chapter = item.get('chapter', '')
    title = item.get('title', '')
    content = item.get('content', '')
    
    input_text = f"Chapter: {chapter}\nTitle: {title}\nContent: {content}"

    # 너무 짧은 데이터 필터링 (노이즈 제거)
    if len(content) < 10:
        return {}

    # 프롬프트 정의 (카테고리 분류 기능 추가)
    prompt = f"""
    아래 내용을 바탕으로 사용자 질문(question)과 답변(answer) 1쌍을 생성해.
    또한 내용의 주제를 파악해서 적절한 카테고리(category)를 단어 1개로 추출해줘. (예: 규정, 절차, 시스템, 일반 등)
    
    반드시 아래 JSON 형식으로만 출력해.
    {{
      "question": "생성된 질문",
      "answer": "생성된 답변",
      "category": "추출된 카테고리"
    }}

    내용:
    {input_text[:2000]}
    """

    # LLM 호출
    try:
        response = llm.invoke([
            SystemMessage(content="너는 데이터셋 생성을 돕는 AI야. 반드시 유효한 JSON만 출력해."),
            HumanMessage(content=prompt)
        ])
        
        qa = _extract_json(response.content)  # JSON 파싱
    except Exception as e:
        print(f"LLM 변환 중 에러 발생: {e}")
        return {}

    # 결과 검증 및 메타데이터(Metadata) 부착
    # 원본 데이터의 정보를 결과물에 꼬리표로 붙여줍니다.
    if "question" in qa and "answer" in qa:
        qa["source"] = item.get("source")   # 파일명 (loader.py에서 가져옴)
        qa["title"] = title                 # 원본 소제목 (검색 시 활용)
        qa["chapter"] = chapter             # 챕터 정보 (필터링 시 활용)
        
        # category는 위에서 AI가 생성했으므로 그대로 둠 (혹은 강제로 지정 가능)
        if "category" not in qa:
            qa["category"] = "General"
            
        return qa

    return {}