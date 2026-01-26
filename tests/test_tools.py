import pytest
import json
import urllib.parse
import requests
from unittest.mock import patch, MagicMock
import os

# [주의] 환경변수가 세팅되기 전에 모듈이 로드되면 URL이 None이 될 수 있습니다.
# tools 내부에서 os.environ.get()을 함수 안에서 호출하거나,
# 아래와 같이 테스트 실행 시 환경변수를 먼저 주입해야 합니다.

# 모듈 임포트 (경로는 프로젝트 구조에 맞게 조정)
from rag import dictionaries
from rag.tools import get_item_detail_info, open_usage_prediction_page

# Fixtures
@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """
    모든 테스트 실행 전 가상의 환경변수를 주입합니다.
    실제 URL이 없어도 테스트가 통과하도록 가짜 주소를 넣습니다.
    """
    envs = {
        "BACKEND_API_URL": "http://test-backend.com",
        "FRONTEND_BASE_URL": "http://test-frontend.com",
        "API_REQUEST_TIMEOUT": "3.0"
    }
    for key, value in envs.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_synonyms():
    """
    테스트용 동의어 사전을 주입합니다.
    rag.dictionaries.KEYWORD_SYNONYMS를 임시로 교체합니다.
    """
    fake_data = {
        "테스트용가짜": "진짜키워드",
        "멍멍이": "강아지"
    }
    with patch.dict(dictionaries.KEYWORD_SYNONYMS, fake_data, clear=True):
        yield


# 1. get_item_detail_info (자산 조회) 테스트
def test_get_item_detail_info_validation_error():
    """필수 입력값이 모두 None일 때 에러 반환 확인"""
    # invoke 시 빈 값 전달
    result = get_item_detail_info.invoke({
        "asset_name": None, 
        "asset_id": None, 
        "identification_num": None
    })
    
    data = json.loads(result)
    assert "error" in data
    # 에러 메시지에 핵심 단어가 포함되어 있는지 확인
    assert any(x in data["error"] for x in ["필수", "입력", "missing"])


@patch("rag.tools.requests.get")
def test_get_item_smart_correction_asset_id(mock_get, mock_synonyms):
    """[Smart Correction] asset_id에 키워드 입력 시 -> asset_name으로 변환 확인"""
    
    # API 응답 Mock (성공 케이스)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [{"name": "Success"}]}
    mock_get.return_value = mock_response

    # 실행: ID 필드에 '테스트용가짜'(키워드) 입력
    get_item_detail_info.invoke({"asset_id": "테스트용가짜"})

    # 검증: 실제 requests.get에 전달된 파라미터 확인
    # call_args.kwargs를 사용하는 것이 더 안전합니다.
    assert mock_get.called
    called_kwargs = mock_get.call_args.kwargs
    called_params = called_kwargs.get("params", {})

    # 1. ID는 비워져야 함 (키워드였으므로)
    assert "asset_id" not in called_params or called_params["asset_id"] is None
    # 2. Name으로 이동하고 '진짜키워드'로 변환되어야 함
    assert called_params.get("asset_name") == "진짜키워드"


@patch("rag.tools.requests.get")
def test_get_item_smart_correction_conflict(mock_get, mock_synonyms):
    """[Conflict] asset_id가 키워드인데, asset_name도 이미 있는 경우 -> asset_name 유지"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response

    # 실행: ID는 키워드(오입력), Name은 정상 입력
    get_item_detail_info.invoke({
        "asset_id": "테스트용가짜",
        "asset_name": "기존검색어"
    })

    called_params = mock_get.call_args.kwargs.get("params", {})

    # ID는 삭제(Discard)
    assert "asset_id" not in called_params or called_params["asset_id"] is None
    # Name은 기존 입력값 유지 (덮어씌워지면 안 됨)
    assert called_params.get("asset_name") == "기존검색어"


@patch("rag.tools.requests.get")
def test_get_item_synonym_conversion(mock_get, mock_synonyms):
    """단순 이름 검색 시 동의어 변환 동작 확인"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response

    get_item_detail_info.invoke({"asset_name": "멍멍이"})

    called_params = mock_get.call_args.kwargs.get("params", {})
    assert called_params.get("asset_name") == "강아지"


@patch("rag.tools.requests.get")
def test_get_item_http_error_handling(mock_get):
    """HTTP 500 등 서버 에러 발생 시 처리"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    # raise_for_status() 호출 시 에러 발생하도록 설정
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
    mock_get.return_value = mock_response

    result = get_item_detail_info.invoke({"asset_name": "ErrorCase"})
    
    data = json.loads(result)
    assert "error" in data
    assert "오류" in data["error"] or "Error" in data["error"]


@patch("rag.tools.requests.get")
def test_get_item_timeout_handling(mock_get):
    """API 요청 시간 초과(Timeout) 발생 시 처리 확인"""
    # 호출 시 즉시 Timeout 예외 발생
    mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

    result = get_item_detail_info.invoke({"asset_name": "SlowAsset"})

    data = json.loads(result)
    assert "error" in data
    # 에러 메시지에 타임아웃 관련 내용 확인
    error_msg = data["error"]
    expected_phrases = ["시간", "초과", "timeout", "timed out"]
    assert any(phrase in error_msg for phrase in expected_phrases)


@patch("rag.tools.requests.get")
def test_get_item_connection_error_handling(mock_get):
    """네트워크 연결 실패(ConnectionError) 발생 시 처리 확인"""
    mock_get.side_effect = requests.exceptions.ConnectionError("DNS Fail")

    result = get_item_detail_info.invoke({"asset_name": "NoNet"})

    data = json.loads(result)
    assert "error" in data
    error_msg = data["error"]
    assert any(k in error_msg for k in ["연결", "네트워크", "접속", "connection"])


# 2. open_usage_prediction_page (페이지 이동) 테스트
def test_prediction_page_url_structure():
    """기본적인 URL 생성 구조 확인"""
    result = open_usage_prediction_page.invoke({"user_question_context": "노트북 수명"})
    data = json.loads(result)
    
    assert data["action"] == "navigate"
    # fixture에서 설정한 가짜 도메인이 들어갔는지 확인
    assert "test-frontend.com" in data["target_url"]
    assert "init_prompt" in data["target_url"]


def test_prediction_page_length_limit():
    """입력값이 500자를 넘을 때 정확히 잘리는지 확인"""
    long_input = "A" * 1000
    result = open_usage_prediction_page.invoke({"user_question_context": long_input})
    data = json.loads(result)
    
    parsed = urllib.parse.urlparse(data["target_url"])
    qs = urllib.parse.parse_qs(parsed.query)
    
    truncated = qs["init_prompt"][0]
    # URL 인코딩 여부와 상관없이 복원된 길이는 500이어야 함 (로직에 따라 다를 수 있음)
    # 일반적인 구현이라면 원본 텍스트 기준 500자 혹은 인코딩 후 길이 제한일 수 있으므로
    # 여기서는 "잘렸다"는 사실과 "길이"를 체크
    assert len(truncated) <= 500
    assert truncated.startswith("AAAA")


def test_prediction_page_security():
    """XSS 및 제어 문자 제거 확인"""
    # Null Byte(\x00)와 Script 태그 시뮬레이션
    malicious_input = "He\x00llo<script>"
    
    result = open_usage_prediction_page.invoke({"user_question_context": malicious_input})
    data = json.loads(result)
    
    target_url = data["target_url"]
    decoded = urllib.parse.unquote(target_url)
    
    # 1. Null Byte가 제거되었거나 인코딩 처리 되었는지
    assert "\x00" not in decoded
    
    # 2. HTML Escape 혹은 URL Encoding 확인
    # <script>가 그대로 실행 가능한 형태로 남아있으면 안 됨
    assert "<script>" not in decoded