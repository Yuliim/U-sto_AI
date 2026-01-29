import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOAD_DIR = os.path.join(BASE_DIR, "data_lifecycle") # 원천 데이터
SAVE_DIR = os.path.join(BASE_DIR, "data_view")      # 뷰 데이터 (create_data/data_view)
os.makedirs(SAVE_DIR, exist_ok=True) # data_view 폴더 생성

# 현재 유효한 상태를 의미하는 종료일 (무기한 유효)
CURRENT_STATUS_END_DATE = pd.Timestamp('2099-12-31')

# ---------------------------------------------------------
# 0. 데이터 로드
# ---------------------------------------------------------
print("📂 [Phase 3] 원천 데이터 로드 중...")

try:
    # Phase 2 결과물
    df_op = pd.read_csv(os.path.join(LOAD_DIR, '04_01_operation_master.csv'))
    df_rt = pd.read_csv(os.path.join(LOAD_DIR, '04_03_return_list.csv'))
    df_du = pd.read_csv(os.path.join(LOAD_DIR, '05_01_disuse_list.csv'))
    df_dp = pd.read_csv(os.path.join(LOAD_DIR, '06_01_disposal_list.csv'))
    df_hist = pd.read_csv(os.path.join(LOAD_DIR, '99_asset_status_history.csv'))

    # 데이터 프레임 전체의 NaN(결측치)를 빈 문자열로 치환 (문자열 컬럼만)
    # 날짜나 숫자는 그대로 두어야 오류가 안 남
    str_cols = ['비고', '운용부서', '운용상태', '승인상태', '사유', '물품상태']
    
    for df in [df_op, df_rt, df_du, df_dp]:
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].fillna('')

except FileNotFoundError as e:
    print(f"❌ 오류: 파일이 없습니다. Phase 1, 2를 먼저 실행해주세요. ({e})")
    exit()
except Exception as e:
    print(f"❌ CSV 로드 중 알 수 없는 오류: {e}")
    exit()

# ---------------------------------------------------------
# 1. 화면별 View CSV 생성
# ---------------------------------------------------------
print("⚙️ [Phase 3] 화면별 요구사항에 따른 View CSV 생성 중...")

# [04-01] 물품 운용 - 물품기본정보 (Grouped View)
print("   - [04-01] 운용 화면용 기본정보 집계 중...")

group_cols_op = [
    'G2B_목록번호', 'G2B_목록명', '캠퍼스','취득일자', '취득금액', '정리일자', 
    '운용부서', '운용상태', '내용연수', '승인상태', 
    '취득정리구분', '운용부서코드', '비고'
]

# 데이터 컬럼 존재 확인
if set(group_cols_op).issubset(df_op.columns):
    view_op_basic = df_op.groupby(group_cols_op).size().reset_index(name='수량')
    view_op_basic.to_csv(os.path.join(SAVE_DIR, 'View_04_01_운용_기본정보.csv'), index=False, encoding='utf-8-sig')
else:
    print("   ⚠️ 경고: 04_01 파일에 필요한 컬럼이 부족합니다.")

# [06-01] 물품 불용/처분 관리 (View 생성 시 안전성 보강)
# Phase 2에서 리스트에 '내용연수' 등을 안 넣었을 수도 있으므로, df_op와 병합하여 정보 채움
print("   - [06-01] 불용 물품 목록 생성 중 (Master 정보 병합)...")

# 병합에 사용할 Master 정보 (변하지 않는 속성)
master_cols = ['물품고유번호', '내용연수', '취득금액', '취득일자', '정리일자', 'G2B_목록명']
df_master_info = df_op[master_cols].drop_duplicates(subset=['물품고유번호'])

# 불용 목록에 Master 정보 병합 (Suffix 방지 위해 컬럼 확인)
# df_du에 이미 있는 컬럼은 제외하고 병합
cols_to_merge = [c for c in master_cols if c not in df_du.columns or c == '물품고유번호']
view_du_item = pd.merge(df_du, df_master_info[cols_to_merge], on='물품고유번호', how='left')

# 필요한 컬럼만 선택
target_cols_du = ['G2B_목록번호', 'G2B_목록명', '물품고유번호', '취득일자', '취득금액', '정리일자', '불용일자','물품상태','내용연수']
# 만약 여전히 없는 컬럼이 있다면 에러 방지
valid_cols_du = [c for c in target_cols_du if c in view_du_item.columns]
view_du_item = view_du_item[valid_cols_du]

view_du_item.to_csv(os.path.join(SAVE_DIR, 'View_06_01_불용물품목록.csv'), index=False, encoding='utf-8-sig')


# [07-01] 보유 현황 조회 (SCD Type 2 History)
print("   - [07-01] 보유 현황(과거 시점 조회용) 데이터 생성 중...")

# 1. 이력 데이터 정렬
df_hist['변경일자'] = pd.to_datetime(df_hist['변경일자'])
df_hist = df_hist.sort_values(by=['물품고유번호', '변경일자'])

# 2. 유효 기간(Start ~ End) 생성
df_hist['유효시작일자'] = df_hist['변경일자']
df_hist['유효종료일자'] = df_hist.groupby('물품고유번호')['변경일자'].shift(-1) - pd.Timedelta(days=1)
df_hist['유효종료일자'] = df_hist['유효종료일자'].fillna(CURRENT_STATUS_END_DATE)

# 3. 속성 정보 결합
# [수정] 정적 정보는 df_op에서 가져오되, 부서 정보는 df_acq에서 가져옴 (반납 시 부서가 사라지므로)
static_cols = [
    'G2B_목록번호', 'G2B_목록명', '물품고유번호', '캠퍼스', '취득일자', '취득금액', '정리일자', 
    '내용연수', '승인상태', '취득정리구분','운용부서', '운용부서코드', '비고'
]
df_static = df_op[static_cols].drop_duplicates(subset=['물품고유번호'])

# 병합
df_scd_raw = pd.merge(df_hist, df_static, on='물품고유번호', how='left')

# 운용부서 빈값 처리 (빈칸 그대로 두거나 '운용부서없음'으로 표시)
df_scd_raw['운용부서'] = df_scd_raw['운용부서'].fillna('')

# 상태값 매핑: 이력 데이터의 '(변경)운용상태'가 그 당시의 실제 상태
df_scd_raw['운용상태'] = df_scd_raw['(변경)운용상태']

# 4. 그룹핑 및 수량 집계
group_cols_scd = [
    'G2B_목록번호', 'G2B_목록명', '캠퍼스',
    '취득일자', '취득금액', '정리일자', 
    '운용부서', '운용상태', '내용연수', '승인상태', 
    '취득정리구분', '운용부서코드', '비고',
    '유효시작일자', '유효종료일자'
]

# 날짜 포맷팅
df_scd_raw['유효시작일자'] = df_scd_raw['유효시작일자'].dt.strftime('%Y-%m-%d')
df_scd_raw['유효종료일자'] = df_scd_raw['유효종료일자'].dt.strftime('%Y-%m-%d')
df_scd_raw = df_scd_raw.fillna('')

view_inventory_scd = df_scd_raw.groupby(group_cols_scd).size().reset_index(name='수량')

# 5. 최종 저장
view_inventory_scd.to_csv(os.path.join(SAVE_DIR, 'View_07_01_보유현황_이력기반.csv'), index=False, encoding='utf-8-sig')

# ---------------------------------------------------------
# 2. 데이터 정합성 검증 (Validation)
# ---------------------------------------------------------
print("\n🔍 [Phase 3] 데이터 정합성 검증 시작")

# 검증 1: 이력 기반 데이터 검증
current_snapshot = view_inventory_scd[view_inventory_scd['유효종료일자'] == '2099-12-31']
total_op = len(df_op)
current_snapshot_qty = pd.to_numeric(current_snapshot['수량'], errors='coerce').sum()

print(f"1. 최신 상태 동기화 검증: 운용대장({total_op}) vs 이력스냅샷({int(current_snapshot_qty)})")
if total_op == current_snapshot_qty:
    print("   ✅ PASS: 일치합니다.")
else:
    print("   ❌ FAIL: 데이터 불일치 발생.")

# 검증 2: 날짜 논리 확인
print("2. 날짜 논리 검증 (취득일자 < 불용일자)")
if not df_du.empty:
    # df_du에 취득일자가 없을 수도 있으므로 df_master_info와 병합된 view_du_item 사용 권장
    df_check = view_du_item.copy()
    df_check['취득일자'] = pd.to_datetime(df_check['취득일자'], errors='coerce')
    df_check['불용일자'] = pd.to_datetime(df_check['불용일자'], errors='coerce')
    
    error_count = (df_check['불용일자'] < df_check['취득일자']).sum()
    
    if error_count == 0:
        print("   ✅ PASS: 시간 순서 정상.")
    else:
        print(f"   ❌ FAIL: {error_count}건 시간 역전.")
else:
    print("   ℹ️ 불용 데이터가 없어 검증 건너뜀.")

print("\n🎉 모든 작업이 완료되었습니다.")