import pandas as pd
import numpy as np
import os
from datetime import datetime

# ---------------------------------------------------------
# 설정 및 데이터 로드
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOAD_DIR = os.path.join(BASE_DIR, "data_lifecycle")
SAVE_DIR = os.path.join(BASE_DIR, "data_ml")
os.makedirs(SAVE_DIR, exist_ok=True)

print("📂 [Phase 4] 데이터 로드 중...")

# 1. 운용 마스터 (전체 물품 목록)
df_op = pd.read_csv(os.path.join(LOAD_DIR, '04_01_operation_master.csv'))

# 2. 불용/처분 목록
df_du = pd.read_csv(os.path.join(LOAD_DIR, '05_01_disuse_list.csv'))

# ---------------------------------------------------------
# 1. 데이터 병합 및 정제 (Data Cleaning)
# ---------------------------------------------------------
print("🧹 1. 데이터 정제 및 병합 수행 중...")

# (1) 운용정보 + 불용정보 병합 (Left Join)
# 병합 전에 '사유' 컬럼명을 명확하게 '불용사유'로 변경합니다.
df_du_subset = df_du[['물품고유번호', '불용일자', '사유']].rename(columns={'사유': '불용사유'})

df_merged = pd.merge(
    df_op, 
    df_du_subset,
    on='물품고유번호', 
    how='left'
)

# (2) 형변환 (String -> Datetime)
date_cols = ['취득일자', '정리일자', '불용일자']
for col in date_cols:
    df_merged[col] = pd.to_datetime(df_merged[col], errors='coerce')

# (3) 결측치 처리
# '정리일자'가 비어있으면 '취득일자'로 대체 (운용 시작 시점)
df_merged['정리일자'] = df_merged['정리일자'].fillna(df_merged['취득일자'])

# (4) 이상치 처리 (예시: 취득금액이 0원 이하인 경우 제외)
df_merged = df_merged[df_merged['취득금액'] > 0].copy()

# ---------------------------------------------------------
# 2. 파생변수 생성 (Feature Engineering)
# ---------------------------------------------------------
print("✨ 2. 파생변수 생성 (Feature Engineering) 중...")

# 기준일자 (현재 시뮬레이션 상의 오늘)
current_date = pd.Timestamp(datetime.now().date())

# [Feature 1] 총 사용 기간
df_merged['관측종료일자'] = df_merged['불용일자'].fillna(current_date)
df_merged['총사용일수'] = (df_merged['관측종료일자'] - df_merged['취득일자']).dt.days

# [Feature 2] 잔여내구연한 (RUL)
df_merged['법적내용연수'] = df_merged['내용연수'] * 365
df_merged['잔여내용연수'] = df_merged['법적내용연수'] - df_merged['총사용일수']

# [Feature 3] 사용 강도 지표 (Usage Intensity)
def calculate_intensity(remark):
    if pd.isna(remark): return 1
    remark = str(remark)
    if any(x in remark for x in ['실습', '공용', '서버', '네트워크']):
        return 3 # 가혹 조건
    elif any(x in remark for x in ['연구', '업무', '디자인']):
        return 2 # 일반 조건
    else:
        return 1 # 단순 보관/기타

df_merged['사용강도'] = df_merged['비고'].apply(calculate_intensity)

# [Feature 4] 고장 발생 플래그 (Failure Flag)
# 💡 [수정 포인트] 위에서 변경한 '불용사유' 컬럼을 사용합니다.
df_merged['고장발생여부'] = df_merged['불용사유'].apply(lambda x: 1 if x == '고장/파손' else 0)

# [Feature 5] 가격대별 가중치 (log scale)
df_merged['취득금액_Log'] = np.log1p(df_merged['취득금액'])

# ---------------------------------------------------------
# 3. 데이터 분할 (Train / Valid / Test)
# ---------------------------------------------------------
print("✂️ 3. 시계열 기준 데이터 분할 (7:2:1)...")

# (1) 시간 순 정렬
df_sorted = df_merged.sort_values(by='취득일자').reset_index(drop=True)

# (2) 인덱스 계산
n_total = len(df_sorted)
n_train = int(n_total * 0.7)
n_valid = int(n_total * 0.2)

# (3) 데이터 자르기
train_set = df_sorted.iloc[:n_train]
valid_set = df_sorted.iloc[n_train : n_train + n_valid]
test_set  = df_sorted.iloc[n_train + n_valid :]

print(f"   - 전체 데이터: {n_total}건")
print(f"   - Train Set : {len(train_set)}건")
print(f"   - Valid Set : {len(valid_set)}건")
print(f"   - Test Set  : {len(test_set)}건")

# ---------------------------------------------------------
# 4. 결과 저장
# ---------------------------------------------------------
model_cols = [
    '물품고유번호', 'G2B_목록명', '물품분류명',
    '취득금액', '취득금액_Log', '내용연수', '사용강도', 
    '취득일자', '불용일자', '총사용일수', '잔여내용연수', '고장발생여부',
    '운용부서'
]
available_cols = [c for c in model_cols if c in df_sorted.columns]

train_set[available_cols].to_csv(os.path.join(SAVE_DIR, 'train.csv'), index=False, encoding='utf-8-sig')
valid_set[available_cols].to_csv(os.path.join(SAVE_DIR, 'valid.csv'), index=False, encoding='utf-8-sig')
test_set[available_cols].to_csv(os.path.join(SAVE_DIR, 'test.csv'), index=False, encoding='utf-8-sig')

print("✅ 모든 작업 완료! 'data_ml' 폴더를 확인하세요.")