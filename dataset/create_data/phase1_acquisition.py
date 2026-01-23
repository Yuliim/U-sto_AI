import os
import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "data_lifecycle")
os.makedirs(SAVE_DIR, exist_ok=True) # 폴더가 없으면 생성
# ---------------------------------------------------------
# 0. 설정 및 초기화
# ---------------------------------------------------------
fake = Faker('ko_KR')  # 한국어 더미 데이터 생성기
TOTAL_COUNT = 5000     # 생성할 데이터 개수 (약 5000건)

# 승인 상태 비율 설정 (확정 89%, 대기 10%, 반려 1%)
APPROVAL_RATIOS = [0.89, 0.10, 0.01]
APPROVAL_STATUSES = ['확정', '대기', '반려']

# ---------------------------------------------------------
# 1. 마스터 데이터 정의 (Master Data)
# ---------------------------------------------------------
# 1-1. G2B 품목 마스터 (17개 표준 품목)
# 구조: [물품분류코드(8), 물품식별코드(8), 품목명, 분류명, 내용연수, 평균단가(원)]
G2B_MASTER_DATA = [
    # IT 기기
    ("43211503", "26103121",
     "노트북컴퓨터, Asus, (CN)B3605CCA-CP0004X, Intel Core Ultra 7 255H(2GHz), 액세사리별도",
     "노트북컴퓨터", 6, 1800000),

    ("43211507", "26111329",
     "데스크톱컴퓨터, 한성컴퓨터, K15-5B71651V0, (내)Ultra 5 235(3.4GHz)/(외)Ultra 5 225(3.3GHz)",
     "데스크톱컴퓨터", 5, 1200000),

    ("43211902", "26108810",
     "액정모니터, 알파스캔디스플레이, (CN)16T20, 39.5cm",
     "액정모니터", 5, 250000),

    ("43222610", "25578661",
     "허브, Belkin, (US)INC002, 7port",
     "허브", 5, 90000),

    ("45111601", "25414806",
     "포인터, 초이스테크놀로지, XPM180Y, 유효거리 50m",
     "포인터", 5, 60000),

    ("43201803", "26048280",
     "하드디스크드라이브, Lenovo, (CN)4XB7A88027, 22TB",
     "하드디스크드라이브", 6, 750000),

    ("43222609", "26066170",
     "라우터, Netgear, (US)PR60X",
     "라우터", 6, 550000),

    ("43202005", "25605835",
     "플래시메모리저장장치, Sandisk, (CN)EXTREME PRO SDXC, 64GB",
     "플래시메모리저장장치", 4, 40000),

    ("43211711", "26101603",
     "스캐너, Kodak alaris, (CN)E1040, 600dpi",
     "스캐너", 6, 900000),

    ("44101601", "26057578",
     "종이절단기, Siser north america, (CN)Romeo, 920×180×200mm",
     "종이절단기", 8, 650000),

    # 가구 및 수납
    ("56101703", "26113315",
     "책상, 신흥, SH-DEAGB11, 1180×780×600~1130mm, 1인용",
     "책상", 10, 350000),

    ("56112102", "26112769",
     "작업용의자, 에코우드, ECO-L003H, 610×680×1185mm",
     "작업용의자", 10, 220000),

    ("56112108", "24928465",
     "책걸상, 의자공장 플러스, PLU-PL01, 575×700×830mm",
     "책걸상", 10, 180000),

    ("56101597", "25964887",
     "서랍형수납장, 라온시스템가구, D-400-60-2, 500×400×558mm",
     "서랍형수납장", 10, 200000),

    # 교육용 보조장·전자칠판·프린터
    ("56121798", "25656485",
     "칠판보조장, 정운시스템, JWBB18212, (부품)전자칠판거치판, 1800×235×1200mm",
     "칠판보조장", 10, 800000),

    ("44111911", "26082440",
     "인터랙티브화이트보드, 보성전자, BSI-P24K, 59.94cm, 전자유도방식/전자펜/전자교탁형",
     "인터랙티브화이트보드", 7, 2981000),

    ("43212105", "25911926",
     "레이저프린터, Ricoh, (CN)P 310, A4/흑백/32ppm",
     "레이저프린터", 5, 350000),
]


# 1-2. 부서 마스터 (조직도)
DEPT_MASTER_DATA = [
    ("C354", "소프트웨어융합대학RC행정팀(ERICA)"),
    ("C352", "공학대학RC행정팀(ERICA)"),
    ("C364", "경상대학RC행정팀(ERICA)"),
    ("C360", "글로벌문화통상대학RC행정팀(ERICA)"),
    ("A351", "시설팀(ERICA)"),
    ("A320", "학생지원팀(ERICA)"),
]
# ---------------------------------------------------------
# 2. 데이터 생성 로직 (Phase 1)
# ---------------------------------------------------------
acquisition_list = []

print(f"🚀 [Phase 1] 물품 취득 데이터 {TOTAL_COUNT}건 생성을 시작합니다...")

for i in range(TOTAL_COUNT):
    # 1) 기본 정보 선택
    g2b_item = random.choice(G2B_MASTER_DATA)
    dept = random.choice(DEPT_MASTER_DATA)
    
    # G2B 정보 언패킹
    class_code, id_code, item_name, class_name, life_years, base_price = g2b_item
    g2b_full_code = class_code + id_code # 16자리 목록번호
    
    # 2) 승인 상태 결정 (89:10:1)
    approval_status = np.random.choice(APPROVAL_STATUSES, p=APPROVAL_RATIOS)
    
    # 3) 날짜 생성 로직
    # 기준: 2015-01-01 ~ 2025-12-31
    start_date_range = datetime(2015, 1, 1)
    end_date_range = datetime.now()
    
    # '대기' 상태는 최근(2024년 10월 이후)에 몰려있도록 설정
    if approval_status == '대기':
        wait_start = datetime(2024, 10, 1)
        acq_date = fake.date_between(start_date=wait_start, end_date=datetime.now())
    else:
        acq_date = fake.date_between(start_date=start_date_range, end_date=end_date_range)
    
    # 4) 정리일자 생성
    # 확정: 취득일 + (1일~7일) 혹은 (1달~2달)
    # 대기/반려: NULL (None)
    clear_date = None
    if approval_status == '확정':
        delay_type = random.choice(['short', 'long'])
        if delay_type == 'short':
            days_add = random.randint(1, 7)
        else:
            days_add = random.randint(30, 60)
        clear_date = acq_date + timedelta(days=days_add)

        # 정리일자는 현재 날짜를 초과하지 않도록 제한
        today = datetime.now().date()

        if isinstance(clear_date, datetime):
            clear_dt = clear_date.date()
        else:
            clear_dt = clear_date

        if clear_dt is not None and clear_dt > today:
            clear_date = today

    
    # 5) 수량 및 금액 생성
    # 취득 단계에서는 '묶음'으로 들어옴 (수량 N개 가능)
    # PC/노트북은 보통 1~10대, 책상은 10~50대 등 품목별 차이 반영
    if "책상" in item_name or "의자" in item_name:
        quantity = random.randint(5, 50)
    else:
        quantity = random.randint(1, 10)
        
    # 취득금액 = (단가 * 수량) + 랜덤 노이즈(옵션가 등)
    unit_price = int(base_price * random.uniform(0.9, 1.1)) # 단가 ±10% 변동
    total_amount = unit_price * quantity
    total_amount = (total_amount // 1000) * 1000 # 1000원 단위 절삭
    
    # 6) 기타 속성 (취득정리구분)
    acq_method = np.random.choice(
        ['자체구입', '자체제작', '기증'],
        p=[0.95, 0.02, 0.03]
    )

    REMARK_TEMPLATES_BY_CLASS = {
    # IT / 전산 장비
    "노트북컴퓨터": [
        "AI 실습 수업용 노트북",
        "전산 실습실 공용 장비",
        "교수·연구원 업무용",
        "학과 공용 전산 자산"
    ],
    "데스크톱컴퓨터": [
        "전산 실습실 고정형 PC",
        "연구실 분석 업무용",
        "행정 업무용 데스크톱"
    ],
    "액정모니터": [
        "전산 실습실 보조 모니터",
        "사무환경 개선용",
        "연구실 다중 화면 구성용"
    ],
    "허브": [
        "전산망 확충용",
        "실습실 네트워크 구성용"
    ],
    "라우터": [
        "실습실 네트워크 증설",
        "학과 전산망 고도화"
    ],
    "하드디스크드라이브": [
        "연구 데이터 저장용",
        "서버 증설용 스토리지"
    ],
    "플래시메모리저장장치": [
        "교육 자료 배포용",
        "백업 매체"
    ],
    "스캐너": [
        "행정 문서 전산화",
        "자료 디지털 아카이빙"
    ],
    "레이저프린터": [
        "행정 문서 출력용",
        "학과 공용 프린터"
    ],

    # 가구 / 집기
    "책상": [
        "강의실 환경 개선",
        "연구실 집기 교체",
        "신규 연구실 구축"
    ],
    "작업용의자": [
        "사무환경 개선",
        "노후 집기 교체"
    ],
    "책걸상": [
        "강의실 집기 교체",
        "노후 책걸상 교체"
    ],
    "서랍형수납장": [
        "연구실 문서 보관용",
        "행정 자료 수납용"
    ],

    # 교육 기자재
    "칠판보조장": [
        "강의실 기자재 보강",
        "노후 기자재 교체"
    ],
    "인터랙티브화이트보드": [
        "스마트 강의실 구축",
        "디지털 강의 환경 개선"
    ],
}
    # 비고 생성
    remark = ""
    if approval_status == '반려':
        remark = "예산 초과로 인한 반려"
    elif random.random() < 0.1:  # 10% 확률로 비고 생성
        # 물품 분류에 맞는 비고 템플릿 선택
        candidates = REMARK_TEMPLATES_BY_CLASS.get(class_name, [])
        if candidates:
            remark = random.choice(candidates)


    # 7) 리스트에 추가 (매뉴얼 속성 매핑)
    row = {
        # 식별 정보
        'G2B_목록번호': g2b_full_code,
        'G2B_목록명': item_name,
        # G2B 상세 (조회용)
        '물품분류코드': class_code,
        '물품분류명': class_name,
        '물품식별코드': id_code,
        '물품품목명': item_name, 
        
        # 취득 정보
        '취득일자': acq_date,
        '취득금액': total_amount,
        '정리일자': clear_date,
        '취득정리구분': acq_method,
        
        # 관리 정보
        '운용부서': dept[1],
        '운용부서코드': dept[0], # 매뉴얼상 같은 값
        '운용상태': '취득', # 취득 대장 상에서는 초기값 '취득'
        '내용연수': life_years,
        '수량': quantity,
        '승인상태': approval_status,
        '비고': remark
    }
    acquisition_list.append(row)

# DataFrame 변환
df_acquisition = pd.DataFrame(acquisition_list)

# 날짜 포맷팅 (YYYY-MM-DD)
df_acquisition['취득일자'] = pd.to_datetime(df_acquisition['취득일자']).dt.strftime('%Y-%m-%d')
df_acquisition['정리일자'] = pd.to_datetime(df_acquisition['정리일자']).dt.strftime('%Y-%m-%d')
df_acquisition['정리일자'] = df_acquisition['정리일자'].replace('NaT', '') # NULL 처리

# ---------------------------------------------------------
# 3. 결과 저장 (CSV Export)
# ---------------------------------------------------------

# [03-01] 물품 취득 대장 목록 (Main Output)
# 필요한 컬럼만 추출하여 저장
cols_acquisition = [
    'G2B_목록번호', 'G2B_목록명', '취득일자', '취득금액', '정리일자', 
    '운용부서', '운용상태', '내용연수', '수량', '승인상태', 
    '취득정리구분', '운용부서코드', '비고'
]
df_acquisition[cols_acquisition].to_csv(os.path.join(SAVE_DIR, '03_01_acquisition_master.csv'), index=False, encoding='utf-8-sig')

# [03-02] G2B 목록 조회용 (Popup Output)
# 분류 목록 (중복 제거)
df_class = df_acquisition[['물품분류코드', '물품분류명']].drop_duplicates()
df_class.to_csv(os.path.join(SAVE_DIR, '03_02_g2b_class_list.csv'), index=False, encoding='utf-8-sig')

# 품목 목록 (중복 제거)
df_item = df_acquisition[['물품식별코드', '물품품목명', '물품분류코드']].drop_duplicates()
df_item.to_csv(os.path.join(SAVE_DIR, '03_02_g2b_item_list.csv'), index=False, encoding='utf-8-sig')

print("✅ [Phase 1] 데이터 생성 완료!")
print(f"   - 총 {len(df_acquisition)}건의 취득 데이터가 생성되었습니다.")
print("   - 저장 파일: 03_01_acquisition_master.csv, 03_02_g2b_class_list.csv, 03_02_g2b_item_list.csv")
print("   - 승인 상태 분포:")
print(df_acquisition['승인상태'].value_counts())