import os
import json
import glob
import sys
import io
import re
import traceback
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# ==========================================
# [침묵 모드] 화면 출력 인코딩 강제 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')
# ==========================================

# [필수] 윈도우 사용자 이름 오류 방지
# 참고: 이 해결 방법은 Windows에서만, 그리고 변수가 누락된 경우에만 적용하십시오.
# 다중 사용자/CI 환경에서 실제 사용자 컨텍스트를 덮어쓰는 것을 방지하기 위함입니다.
if os.name == "nt":
    if "USERNAME" not in os.environ:
        os.environ["USERNAME"] = "User"
    if "USER" not in os.environ:
        os.environ["USER"] = "User"

# [필수] API 키 가져오기
load_dotenv()  # .env 파일을 os.environ에 로드 (정석 방법)


INPUT_FOLDER = 'dataset/input'
OUTPUT_FOLDER = 'dataset/qa_output'

def extract_json_from_text(text):
    try:
        # 1. 가장 쉬운 경우: 그냥 바로 변환 시도
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # 2. Markdown 코드블록 제거 (```json ... ```)
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # 3. 정규표현식으로 { ... } 구간만 강제로 추출
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    json_str = match.group()
                    return json.loads(json_str)
            except json.JSONDecodeError:
                return None
    return None

def convert_content_to_qa():
    print("Smart Converting Started...") 

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # temperature=0.1 : 창의성을 줄이고 형식을 더 잘 지키게 함
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
    input_files = glob.glob(os.path.join(INPUT_FOLDER, '*.json'))

    if not input_files:
        print("Error: No input files found.")
        return

    print(f"Found {len(input_files)} files. Processing...")

    for file_idx, file_path in enumerate(input_files, start=1):
        file_name = os.path.basename(file_path)
        print(f"\nProcessing File: {file_idx}/{len(input_files)} ({file_name})")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            new_qa_data = []
            total_items = len(data)

            for idx, item in enumerate(data):
                try:
                    # 데이터 텍스트화
                    if isinstance(item, dict):
                        title = item.get('title', '')
                        content = item.get('content', '')
                        # 내용이 너무 짧으면(10자 미만) 건너뛰기 (불필요한 에러 방지)
                        full_text = f"{title} {content}".strip()
                        if len(full_text) < 10:
                            print(f"[SKIP] Item {idx+1} (Too short)")
                            continue
                            
                        input_text = f"Title: {title}\nContent: {content}"
                    else:
                        input_text = str(item)
                        if len(input_text) < 10:
                            print(f"[SKIP] Item {idx+1} (Too short)")
                            continue

                    # 프롬프트 강화: 무조건 JSON만 뱉으라고 협박(?)
                    prompt_text = f"""
                    You are a data converter. 
                    Read the text below and create ONE question and answer pair in Korean.
                    
                    RULES:
                    1. Output MUST be valid JSON format only.
                    2. Keys must be "question" and "answer".
                    3. Do not add any explanation or markdown. Just the JSON.
                    
                    [Source Text]:
                    {input_text[:1500]} 
                    """

                    # AI 호출
                    response = llm.invoke([
                        SystemMessage(content="Output valid JSON only. No markdown."),
                        HumanMessage(content=prompt_text)
                    ])

                    # 결과 추출 (강력한 함수 사용)
                    qa_dict = extract_json_from_text(response.content)

                    if qa_dict and "question" in qa_dict and "answer" in qa_dict:
                        final_data = {
                            "question": qa_dict.get("question", ""),
                            "answer": qa_dict.get("answer", ""),
                            "source": file_name
                        }
                        new_qa_data.append(final_data)
                        print(f"[OK] Item {idx+1}/{total_items} success.")
                    else:
                        # JSON 구조는 아니지만 응답은 왔을 때
                        print(f"[FAIL] Item {idx+1} JSON Parsing Error.")

                except Exception as e:
                    # 진짜 네트워크/API 에러인 경우
                    # 1. 에러 메시지(e)를 포함하여 출력
                    print(f"[ERROR] Item {idx+1} API/System Error: {e}")
    
                    # 2. 어디서 에러가 났는지 상세 경로(Traceback) 출력
                    print("--- Error Detail ---")
                    print(traceback.format_exc())
                    print("--------------------")

            # 파일 저장
            if new_qa_data:
                output_path = os.path.join(OUTPUT_FOLDER, file_name)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(new_qa_data, f, ensure_ascii=False, indent=2)
                print(f"--> Saved {len(new_qa_data)} items to file.")
            else:
                print("--> No valid data to save.")

        except Exception as e:
            print(f"--> File Error (Skipped): {e}")

    print("\nAll Done! Check 'dataset/qa_output' folder.")

if __name__ == "__main__":
    convert_content_to_qa()