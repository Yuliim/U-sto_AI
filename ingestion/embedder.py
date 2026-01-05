#  # 벡터 생성 로직

# QA 텍스트 → 벡터 변환
# OpenAI / HuggingFace embedding 연결 지점

from langchain_openai import OpenAIEmbeddings  # 임베딩 클래스

def get_embedding_model():
    # 임베딩 모델 생성 함수
    return OpenAIEmbeddings(
        model="text-embedding-3-small"  # 비용 대비 성능 우수 모델
    )
