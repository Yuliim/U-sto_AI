# JSON 파일 로딩 및 Chunking 역할
# dataset_sample의 원본 지식 읽기 담당

import json  # JSON 파싱 모듈
import os    # 파일 경로 처리 모듈
from typing import List, Dict  # 타입 힌트용

# Chunking 규칙 함수 정의 (여기서 규칙을 수정합니다)
def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    긴 텍스트를 chunk_size 길이로 자르되, 문맥 유지를 위해 overlap만큼 겹치게 자릅니다.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        # 단순히 글자 수로 자르면 단어가 잘릴 수 있으므로 여유가 된다면 공백 기준으로 조정 가능
        # 여기서는 심플하게 글자 수(chunk_size)로 자릅니다.
        chunk = text[start:end]
        chunks.append(chunk)
        
        # 다음 청크는 overlap만큼 겹쳐서 시작 (문맥 끊김 방지)
        start += (chunk_size - overlap)
        
    return chunks

# 메인 로더 함수
def load_json_files(folder_path: str) -> List[Dict]:
    # 지정된 폴더 내 JSON 파일들을 모두 로드하는 함수
    documents = []  # 결과 저장 리스트 초기화

    # 폴더 내 파일 순회
    for file_name in os.listdir(folder_path):
        # JSON 파일만 처리
        if not file_name.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, file_name)  # 전체 경로 생성

        # 파일 열기
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)  # JSON 로드

            # 각 아이템 순회
            for item in data:
                origin_text = item.get("content", "") 
                
                # 텍스트가 비어있으면 스킵
                if not origin_text:
                    continue

                # 위에서 만든 규칙대로 텍스트 자르기 (Chunking)
                text_chunks = split_text(origin_text, chunk_size=500, overlap=50)

                # 잘라진 조각들을 각각 별도의 문서로 저장
                for chunk in text_chunks:
                    new_doc = item.copy()  # 원본 메타데이터 복사
                    new_doc["content"] = chunk # 본문을 잘라진 조각으로 교체
                    new_doc["source"] = file_name # 출처 기록
                    
                    documents.append(new_doc)      # 리스트에 추가

    return documents  # 로드된 전체 문서 반환