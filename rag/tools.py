import os
import json
import requests  # 실제 API 호출용 (없으면 pip install requests)
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일 읽기)
load_dotenv()

# 환경 변수에서 주소 가져오기 (없으면 None)
API_SERVER_URL = os.getenv("ASSET_API_SERVER_URL")
DASHBOARD_BASE_URL = os.getenv("DASHBOARD_BASE_URL", "http://localhost:3000") # 기본값 설정

# [Fallback용 Mock Data]
# API 호출 실패 시 또는 개발용으로 사용
MOCK_ASSET_DB = [
    {
        "id": "A-1001", "name": "맥북 프로 16인치", "status": "사용 중 (양호)",
        "dept": "IT 개발팀", "date": "2023-01-15", "desc": "고성능 개발 장비"
    },
    {
        "id": "A-1002", "name": "팀장님 의자", "status": "수리 필요 (파손)",
        "dept": "경영지원팀", "date": "2020-05-10", "desc": "허리 받침대 고장"
    }
]


# 1. 물품 기본 정보 조회 함수
def get_asset_basic_info(asset_name: str = None, asset_id: str = None) -> str:
    """
    [기능] 물품명이나 ID로 자산을 검색하여 기본 정보를 반환합니다.
    [로직] .env에 API 주소가 있으면 실제 호출, 없으면 Mock 데이터 사용
    """
    print(f"\n[Tool 실행] get_asset_basic_info 호출됨 (Name={asset_name}, ID={asset_id})")

    # [Option A] 실제 백엔드 API 호출 시도
    if API_SERVER_URL:
        try:
            # 실제 API 스펙에 맞춰 수정 필요 (예시: GET /api/assets?name=...)
            params = {}
            if asset_name: params["name"] = asset_name
            if asset_id: params["id"] = asset_id

            # 타임아웃 3초 설정 (너무 오래 걸리면 Mock으로 넘기기 위해)
            response = requests.get(f"{API_SERVER_URL}/api/assets", params=params, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                # 여기서 백엔드 응답을 AI가 좋아하는 포맷으로 변환해야 함
                # (백엔드 응답 구조에 따라 수정 필요)
                return json.dumps(data, ensure_ascii=False)
            else:
                print(f"[API Error] Status: {response.status_code}")

        except Exception as e:
            print(f"[API Connection Failed] {e}")
            print(">> 백엔드 연결 실패, Mock 데이터를 대신 사용합니다.")

    # [Option B] Fallback: Mock Data 사용 (API 실패/미설정 시)
    found_item = None
    for item in MOCK_ASSET_DB:
        if asset_id and asset_id == item["id"]:
            found_item = item
            break
        if asset_name and asset_name in item["name"]:
            found_item = item
            break
            
    if found_item:
        result = {
            "asset_name": found_item["name"],
            "current_status": found_item["status"],
            "department": found_item["dept"],
            "acquisition_date": found_item["date"],
            "summary_text": f"요청하신 '{found_item['name']}'은(는) 현재 {found_item['dept']}에서 관리 중이며, 상태는 '{found_item['status']}'입니다."
        }
        return json.dumps(result, ensure_ascii=False)

    return json.dumps({"error": "해당하는 물품 정보를 찾을 수 없습니다."}, ensure_ascii=False)


# 2. 메뉴/화면 이동 함수
def navigate_to_page(page_type: str) -> str:
    print(f"\n[Tool 실행] navigate_to_page 호출됨 (Page={page_type})")
    
    # URL 경로 매핑
    path_map = {
        "ASSET_DETAIL": "/assets/detail",
        "USAGE_PREDICTION": "/analysis/prediction",
        "DISPOSAL_MANAGEMENT": "/assets/disposal"
    }
    
    path = path_map.get(page_type, "/home")
    # 환경변수(DASHBOARD_BASE_URL)와 경로 결합
    full_url = f"{DASHBOARD_BASE_URL}{path}"
    
    result = {
        "success": True,
        "target_url": full_url,
        "message": f"{page_type} 화면으로 이동합니다."
    }
    return json.dumps(result, ensure_ascii=False)


# 3. 사용주기 예측 페이지 연결 함수
def open_usage_prediction_page(keyword: str = "") -> str:
    print(f"\n[Tool 실행] open_usage_prediction_page 호출됨 (Keyword={keyword})")
    
    path = "/analysis/prediction"
    base_url = f"{DASHBOARD_BASE_URL}{path}"
    
    if keyword:
        target_url = f"{base_url}?search={keyword}"
        msg = f"'{keyword}'에 대한 수명 예측 분석 화면을 열어드립니다."
    else:
        target_url = base_url
        msg = "수명 예측 분석 대시보드로 이동합니다."
        
    result = {
        "target_url": target_url,
        "guide_msg": msg
    }
    return json.dumps(result, ensure_ascii=False)