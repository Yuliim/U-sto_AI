# (1) 물품 기본 정보 조회 Function Schema
# 최소한의 파라미터로 AI 느낌 유지, 수치/계산 필드 제외

GET_ASSET_BASIC_INFO_SCHEMA = {
    "name": "get_asset_basic_info",
    "description": "물품의 이름이나 고유번호를 통해 현재 상태, 운용 부서, 취득 일자 등의 기본 정보를 조회합니다. 수명 예측이나 분석 데이터는 포함하지 않습니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "asset_name": {
                "type": "string",
                "description": "사용자가 언급한 물품의 이름 (예: '맥북 프로', '13층 복합기', '팀장님 의자')"
            },
            "asset_id": {
                "type": "string",
                "description": "물품의 고유 관리 번호 (식별 가능한 경우, 예: 'A-1234')"
            }
        },
        "required": []
    }
}


# (2) 메뉴/화면 이동 Function Schema
# 특정 기능(상세, 예측, 불용) 화면으로 사용자를 안내

NAVIGATE_TO_PAGE_SCHEMA = {
    "name": "navigate_to_page",
    "description": "사용자가 물품 상세 정보 확인, 수명 예측 분석, 또는 불용(폐기) 관리 등의 작업을 원할 때 적절한 시스템 화면으로 이동하거나 안내합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "page_type": {
                "type": "string",
                "enum": ["ASSET_DETAIL", "USAGE_PREDICTION", "DISPOSAL_MANAGEMENT"],
                "description": "이동할 페이지 유형 (ASSET_DETAIL: 물품 상세, USAGE_PREDICTION: 수명/사용주기 예측, DISPOSAL_MANAGEMENT: 불용/폐기 관리)"
            }
        },
        "required": ["page_type"]
    }
}


# (3) 사용주기 AI 예측 연결 Function Schema
# 챗봇이 직접 분석하지 않고, 전문 분석 화면을 열어주며 키워드 전달"

OPEN_USAGE_PREDICTION_PAGE_SCHEMA = {
    "name": "open_usage_prediction_page",
    "description": "사용자가 물품의 수명 예측, 고장 시점 분석, 또는 사용 주기와 관련된 구체적인 데이터를 보고 싶어 할 때 전문 분석 화면을 엽니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "사용자가 언급한 검색 키워드 또는 물품명 (자연어 그대로 전달, 예: '서버실 에어컨', '김팀장 노트북')"
            }
        },
        "required": []
    }
}


# [최종] 툴 목록 정의 (이 리스트를 LLM에게 전달합니다)
TOOLS_SCHEMA = [
    GET_ASSET_BASIC_INFO_SCHEMA,      # (1) 기본 정보 조회
    NAVIGATE_TO_PAGE_SCHEMA,          # (2) 화면 이동
    OPEN_USAGE_PREDICTION_PAGE_SCHEMA # (3) 예측 페이지 연결
]