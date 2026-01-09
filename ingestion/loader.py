# JSON 파일 로딩 및 Chunking 역할
# dataset_sample의 원본 지식 읽기 담당

import json  # JSON 파싱 모듈
import os    # 파일 경로 처리 모듈
from typing import List, Dict  # 타입 힌트용

# Chunking 규칙 함수 정의 (여기서 규칙을 수정합니다)
def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    
    # [Fix 1] 유효성 검사 추가 (Copilot 지적 사항)
    # chunk_size가 overlap보다 커야 루프가 정상적으로 앞으로 나아갑니다.
    if chunk_size <= overlap:
        raise ValueError(f"chunk_size({chunk_size})는 overlap({overlap})보다 커야 합니다.")
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)

        # 마지막 부분이 아니라면, 단어가 잘리지 않게 뒤에서부터 공백/구두점 탐색
        if end < text_len:
            # end 지점에서부터 overlap 범위 내에서 가장 가까운 공백/마침표 찾기
            # (너무 많이 뒤로 가면 안 되므로 최대 chunk_size의 30%까지만 뒤로 탐색)
            look_back_limit = max(start + 1, end - int(chunk_size * 0.3))
            
            found_split = False
            for i in range(end, look_back_limit, -1):
                if text[i] in [' ', '\n', '.', '!', '?']:
                    end = i + 1  # 공백/구두점 다음에서 자름
                    found_split = True
                    break
            
            # 적절한 분기점을 못 찾았다면 강제로 자름 (기본 end 유지)

        chunk = text[start:end].strip()

        # 빈 청크가 아니면 추가
        if chunk:
            chunks.append(chunk)

        # [Fix 2] 다음 시작점 계산 로직 개선
        # 무한 루프 방지를 위해 반드시 start가 증가하도록 보장
        next_step = end - overlap

        # 겹치는 부분이 현재 시작점보다 뒤에 있어야 함.
        # 만약 청크가 너무 작아서 next_step이 start보다 앞서거나 같다면,
        # 겹치지 않더라도 그냥 end부터 시작하게 함 (무한 루프 방지)
        if next_step <= start: 
            start = end
        else:
            start = next_step
        
        # [Safety Check] 만약 어떤 이유로든 start가 이전과 같거나 줄어들면 강제 종료
        if start >= text_len:
            break
        
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