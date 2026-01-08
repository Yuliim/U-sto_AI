import os
import sys
import io
import json
import shutil
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# ==========================================
# [화면 출력 인코딩 설정]
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')
# ==========================================

# API 키 확인
if not os.getenv("OPENAI_API_KEY"):
    print(" 오류: .env 파일이 없거나 OPENAI_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def main():
    # [설정] 경로 지정
    # 현재 파일 위치 기준
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    # [중요] 타겟 파일 경로 (generate_qa.py의 결과물)
    TARGET_FILE = os.path.join(root_dir, 'dataset/qa_output/manual_qa_final.json')
    
    # DB 저장 경로
    DB_PATH = os.path.join(root_dir, 'chroma_db')

    print("벡터 DB 생성 작업을 시작합니다...")

    # 1. 기존 DB 삭제 (초기화)
    # 기존에 테스트하던 찌꺼기 데이터가 남지 않도록 깔끔하게 지우고 시작합니다.
    if os.path.exists(DB_PATH):
        print(f"기존 DB 폴더('{DB_PATH}')를 초기화합니다...")
        try:
            shutil.rmtree(DB_PATH)
        except Exception as e:
            print(f"경고: 기존 DB 삭제 중 오류 발생 (무시하고 진행합니다): {e}")

    # 2. 데이터 로드
    if not os.path.exists(TARGET_FILE):
        print(f"오류: 파일이 없습니다 -> {TARGET_FILE}")
        print("   먼저 generate_qa.py를 실행해서 데이터를 만들어주세요.")
        sys.exit(1)

    print(f"타겟 파일 로드 중: {os.path.basename(TARGET_FILE)}")
    
    try:
        with open(TARGET_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"JSON 파일 읽기 실패: {e}")
        sys.exit(1)

    # 3. LangChain Document 객체로 변환
    documents = []
    
    if isinstance(data, list):
        for item in data:
            # 질문(Q)과 답변(A) 가져오기
            q = item.get('question', '')
            a = item.get('answer', '')
            
            # 둘 다 내용이 있을 때만 처리
            if q and a:
                # [수정 포인트 1] 검색 내용 구성
                # AI가 검색할 때 '카테고리'와 '제목'도 같이 보면 훨씬 정확해집니다.
                content = f"Category: {item.get('category', 'General')}\nTitle: {item.get('title', '')}\nQ: {q}\nA: {a}"
                
                # [수정 포인트 2] 메타데이터 연결 (우리가 만든 키 값과 일치시킴)
                metadata = {
                    "source": item.get("source", "Unknown"),
                    "title": item.get("title", ""),
                    "chapter": item.get("chapter", ""),
                    "category": item.get("category", "General")
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
    else:
        print("경고: JSON 데이터가 리스트 형식이 아닙니다.")

    if not documents:
        print("변환할 데이터가 없습니다.")
        sys.exit(1)

    print(f"✅ 총 {len(documents)}개의 지식(QA)을 준비했습니다.")

    # 4. 임베딩 및 DB 저장
    print("Embedding 모델을 준비 중입니다...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    print(f"Chroma DB에 저장 중... ({DB_PATH})")
    print("   (데이터 양에 따라 시간이 조금 걸릴 수 있습니다)")
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=DB_PATH
    )

    print("-" * 30)
    print("DB 생성 완료!")
    print(f"이제 '{DB_PATH}' 폴더에 AI의 지식이 저장되었습니다.")

if __name__ == "__main__":
    main()