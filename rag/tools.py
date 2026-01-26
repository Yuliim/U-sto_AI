import json
import logging
import os
import urllib.parse
import requests
import re
import html
from typing import Optional
from rag import dictionaries

from dotenv import load_dotenv
from langchain_core.tools import tool


# 로거 설정
logger = logging.getLogger(__name__)


# .env 파일 로드
load_dotenv()


# 필수 환경변수 로드
BACKEND_API_URL = os.getenv("BACKEND_API_URL")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")
API_REQUEST_TIMEOUT = float(os.getenv("API_REQUEST_TIMEOUT", 5))


# 필수 환경변수 검증 (모듈 임포트 시점에 즉시 실패)
missing_vars = []
if not BACKEND_API_URL: missing_vars.append("BACKEND_API_URL")
if not FRONTEND_BASE_URL: missing_vars.append("FRONTEND_BASE_URL")

if missing_vars:
    error_msg = f"Required environment variables are missing: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)


# [최적화] 모듈 로드 시점에 '소문자 키 -> 표준어' 매핑 테이블을 미리 생성합니다.
_SYNONYM_LOOKUP = {k.lower(): v for k, v in dictionaries.KEYWORD_SYNONYMS.items()}

# 헬퍼 함수 (메모리 효율화 & 중복 로직 제거)
def get_normalized_keyword(input_str: str) -> Optional[str]:
    """
    입력값의 동의어를 찾아 표준어로 변환합니다.
    미리 구성된 해시 테이블(_SYNONYM_LOOKUP)을 사용하여 O(1) 속도로 조회합니다.
    """
    if not input_str:
        return None
        
    # 입력값을 소문자로 변환하여 즉시 조회
    target = input_str.strip().lower()
    
    # .get() 메서드로 키가 없으면 None 반환
    return _SYNONYM_LOOKUP.get(target)


# LangChain 도구 정의
# 1. 물품 특정 정보 조회
@tool
def get_item_detail_info(
    asset_name: Optional[str] = None, 
    asset_id: Optional[str] = None, 
    identification_num: Optional[str] = None
) -> str:
    """
    특정 물품의 G2B목록명, G2B목록번호 또는 물품고유번호를 입력받아,
    API를 통해 해당 물품의 상세 정보를 조회합니다.
    """

    # 1. 기본 입력값 정제 (None 방지 및 공백 제거)
    if asset_name: asset_name = asset_name.strip()
    if asset_id: asset_id = asset_id.strip()
    if identification_num: identification_num = identification_num.strip()

    # 2. 잘못된 입력 위치 자동 보정 (Smart Correction)
    # Case A: asset_id 필드 검사
    if asset_id:
        # 헬퍼 함수를 사용하여 키워드 여부 확인
        if get_normalized_keyword(asset_id) is not None:
            if not asset_name:
                logger.info(
                    f"[Smart Correction] asset_id '{asset_id}' -> asset_name으로 이동 (ID 필드에 키워드 감지)"
                )
                asset_name = asset_id
            else:
                logger.warning(
                    f"[Smart Correction - CONFLICT] asset_id '{asset_id}'가 키워드이지만, "
                    f"asset_name '{asset_name}'이 이미 존재합니다. "
                    f"-> 검색 오류 방지를 위해 asset_id 입력값을 '삭제(Discard)' 합니다."
                )
            asset_id = None

    # Case B: identification_num 필드 검사
    if identification_num:
        if get_normalized_keyword(identification_num) is not None:
            if not asset_name:
                logger.info(
                    f"[Smart Correction] identification_num '{identification_num}' -> asset_name으로 이동"
                )
                asset_name = identification_num
            else:
                logger.warning(
                    f"[Smart Correction - CONFLICT] identification_num '{identification_num}'가 키워드이지만, "
                    f"asset_name '{asset_name}'이 이미 존재합니다. "
                    f"-> 검색 오류 방지를 위해 identification_num 입력값을 '삭제(Discard)' 합니다."
                )
            identification_num = None

    # 필수값 검증 (보정 후 다시 확인)
    if not any((asset_name, asset_id, identification_num)):
        return json.dumps(
            {"error": "검색할 G2B목록명, G2B목록번호, 또는 물품고유번호 중 하나는 필수로 입력해야 합니다."},
            ensure_ascii=False
        )
    
    # 3. 검색어 변환 (Slang -> Standard)
    target_search_name = asset_name
    if asset_name:
        # 삭제된 전역 변수 참조 대신 헬퍼 함수 사용
        standard_name = get_normalized_keyword(asset_name)
        if standard_name:
            target_search_name = standard_name
            logger.info(f"[Synonym Match] '{asset_name}' -> '{target_search_name}'")

    # 4. API 요청 파라미터 구성 및 호출
    params = {}
    if identification_num: params["identification_num"] = identification_num
    if asset_id: params["asset_id"] = asset_id
    if target_search_name: params["asset_name"] = target_search_name

    try:
        api_url = f"{BACKEND_API_URL.rstrip('/')}/search"
        
        response = requests.get(api_url, params=params, timeout=API_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # 검색 결과가 비어있는 경우
        if not data.get("results"):
            msg = "조건에 맞는 물품을 찾을 수 없습니다."
            if asset_name and asset_name != target_search_name:
                msg += f" (참고: '{asset_name}'은(는) '{target_search_name}'(으)로 변환하여 검색했습니다.)"
            return json.dumps({"message": msg}, ensure_ascii=False)

        return json.dumps(data, ensure_ascii=False)

    except json.JSONDecodeError:
        logger.error("API 응답 JSON 파싱 실패", exc_info=True)
        return json.dumps({"error": "서버에서 잘못된 형식의 데이터를 반환했습니다."}, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        # 1. 타임아웃 (Timeout)
        if isinstance(e, requests.exceptions.Timeout):
            logger.error(f"API 요청 시간 초과: {e}")
            return json.dumps(
                {"error": "요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."},
                ensure_ascii=False
            )

        # 2. 연결 실패 (ConnectionError)
        # if 대신 elif를 사용하여 위 조건(Timeout)이 아닐 때만 체크함을 명시
        elif isinstance(e, requests.exceptions.ConnectionError):
            logger.error(f"API 서버 연결 실패: {e}")
            return json.dumps(
                {"error": "현재 자산 조회 시스템에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요."},
                ensure_ascii=False,
            )

        # 3. 그 외 HTTP 에러 (404, 500 등)
        elif isinstance(e, requests.exceptions.HTTPError):
            logger.error(f"API 서버 응답 오류: {e}")
            return json.dumps(
                {"error": "서버에서 오류가 발생했습니다. 관리자에게 문의해 주세요."},
                ensure_ascii=False,
            )
            
        # 4. 기타 알 수 없는 요청 에러
        else:
            logger.error(f"API 요청 중 알 수 없는 오류 발생: {e}")
            return json.dumps(
                {"error": "데이터 조회 중 문제가 발생했습니다."},
                ensure_ascii=False
            )


# 2. 사용주기 예측 페이지 연결
@tool
def open_usage_prediction_page(user_question_context: str) -> str:
    """
    사용자의 질문이 단순 조회를 넘어 예측/분석(수명, 고장, 교체주기 등)이 필요한 경우 호출합니다.
    질문 내용을 분석 페이지로 전달(Deep Link)하여 자동으로 결과가 표시되도록 합니다.
    """
    MAX_CONTEXT_LENGTH = 500
    base_path = f"{FRONTEND_BASE_URL.rstrip('/')}/prediction/analysis/prediction"

    params = {}
    
    if user_question_context:
        if not isinstance(user_question_context, str):
            user_question_context = str(user_question_context)

        # 1. 공백 제거
        cleaned_context = user_question_context.strip()

        # 2. 제어 문자 제거 (Null byte 등)
        cleaned_context = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', cleaned_context)

        # 3. HTML Escape (XSS 방지)
        cleaned_context = html.escape(cleaned_context)
        
        # 4. 길이 제한 및 Edge Case(잘린 엔티티) 처리
        if len(cleaned_context) > MAX_CONTEXT_LENGTH:
            cleaned_context = cleaned_context[:MAX_CONTEXT_LENGTH]
            
            last_amp = cleaned_context.rfind('&')
            last_semi = cleaned_context.rfind(';')

            # 닫히지 않은 엔티티(&... 로 끝나는 경우) 제거
            if last_amp > last_semi:
                cleaned_context = cleaned_context[:last_amp]
        
        if cleaned_context:
            params['init_prompt'] = cleaned_context

    # 파라미터가 있을 때만 쿼리 스트링 생성
    if params:
        query_string = urllib.parse.urlencode(params)
        final_url = f"{base_path}?{query_string}"
    else:
        final_url = base_path

    return json.dumps({
        "action": "navigate",
        "target_url": final_url,
        "guide_msg": "상세 분석이 필요하여 [사용주기 예측] 페이지를 준비했습니다. 링크를 클릭하시면 질문하신 내용에 대한 분석 결과를 바로 확인하실 수 있습니다."
    }, ensure_ascii=False)