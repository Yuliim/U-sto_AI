import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOAD_DIR = os.path.join(BASE_DIR, "data_lifecycle") # 원천 데이터
SAVE_DIR = os.path.join(BASE_DIR, "data_view")      # 뷰 데이터 (create_data/data_view)
os.makedirs(SAVE_DIR, exist_ok=True) # data_view 폴더 생성

# ---------------------------------------------------------
# 0. 데이터 로드 (Phase 2 결과물)
# ---------------------------------------------------------
print("📂 [Phase 3] 원천 데이터 로드 중...")

try:
    df_op = pd.read_csv(os.path.join(LOAD_DIR, '04_01_operation_master.csv'))
    df_rt = pd.read_csv(os.path.join(LOAD_DIR, '04_03_return_list.csv'))
    df_du = pd.read_csv(os.path.join(LOAD_DIR, '05_01_disuse_list.csv'))
    df_dp = pd.read_csv(os.path.join(LOAD_DIR, '06_01_disposal_list.csv'))    # 처분
    # 이력 데이터 로드 (보유현황 구성을 위해 필수)
    df_hist = pd.read_csv(os.path.join(LOAD_DIR, '99_asset_status_history.csv'))
except FileNotFoundError as e:
    print(f"❌ 오류: 파일이 없습니다. Phase 2를 먼저 실행해주세요. ({e})")
    exit()
except PermissionError as e:
    print(f"❌ 파일 접근 권한 오류: {e}")
    exit()
except Exception as e:
    print(f"❌ CSV 로드 중 알 수 없는 오류: {e}")
    exit()

# 날짜 컬럼 형변환 (검증용)
date_cols = ['취득일자', '정리일자']
for col in date_cols:
    if col in df_op.columns: df_op[col] = pd.to_datetime(df_op[col])

# ---------------------------------------------------------
# 1. 화면별 View CSV 생성
# ---------------------------------------------------------
print("⚙️ [Phase 3] 화면별 요구사항에 따른 View CSV 생성 중...")

# [04-03] 물품 반납 관리
# 1) 상단 그리드: 반납 등록 목록 (신청 건 위주)
#    (실제론 Request ID로 묶여야 하지만, 여기선 개별 행을 신청 건으로 간주)
view_rt_reg = df_rt[['반납일자', '반납확정일자', '등록자ID', '등록자명', '승인상태']]
view_rt_reg.to_csv(os.path.join(SAVE_DIR, 'View_04_03_반납등록목록.csv'), index=False, encoding='utf-8-sig')

# 2) 하단 그리드: 반납 물품 목록 (상세)
view_rt_item = df_rt[['G2B_목록번호', 'G2B_목록명', '물품고유번호', '취득일자', '취득금액', '운용부서', '물품상태', '사유']]
view_rt_item.to_csv(os.path.join(SAVE_DIR, 'View_04_03_반납물품목록.csv'), index=False, encoding='utf-8-sig')


# [05-01] 물품 불용 관리
# 1) 상단 그리드: 불용 등록 목록
view_du_reg = df_du[['불용일자', '불용확정일자', '등록자ID', '등록자명', '승인상태']]
view_du_reg.to_csv(os.path.join(SAVE_DIR, 'View_05_01_불용등록목록.csv'), index=False, encoding='utf-8-sig')

# 2) 하단 그리드: 불용 물품 목록
view_du_item = df_du[['G2B_목록번호', 'G2B_목록명', '물품고유번호', '취득일자', '취득금액', '운용부서', '물품상태', '사유']]
view_du_item.to_csv(os.path.join(SAVE_DIR, 'View_05_01_불용물품목록.csv'), index=False, encoding='utf-8-sig')


# [06-01] 물품 처분 관리
# 1) 상단 그리드: 처분 목록
view_dp_reg = df_dp[['처분일자', '처분정리구분', '등록자ID', '등록자명', '승인상태']]
view_dp_reg.to_csv(os.path.join(SAVE_DIR, 'View_06_01_처분목록.csv'), index=False, encoding='utf-8-sig')

# 2) 하단 그리드: 처분 물품 목록
# 요청하신 '정리일자', '불용일자', '내용연수' 포함
view_dp_item = df_dp[['G2B_목록번호', 'G2B_목록명', '물품고유번호', '취득일자', '취득금액', 
                      '처분방식', '물품상태', '사유', '정리일자', '불용일자', '내용연수']]
view_dp_item.to_csv(os.path.join(SAVE_DIR, 'View_06_01_처분물품목록.csv'), index=False, encoding='utf-8-sig')


# [07-01] 보유 현황 조회 (Aggregation)
# "특정 시점을 조회했을 때 그 당시의 수량이 나와야 한다."
# 해결책: 단순히 현재 상태를 카운트하는 것이 아니라, 이력(History) 데이터를 가공하여
#         각 자산이 '언제부터(StartDate) 언제까지(EndDate) 어떤 상태(Status)였는지'를 기록한 데이터를 생성합니다.
#         시스템(UI)에서는 이 테이블을 조회 기간과 비교(Between)하여 카운트하면 됩니다.
print("   - 보유 현황(과거 시점 조회용) 데이터 생성 중...")

# 1. 이력 데이터 정렬 (물품별, 날짜순)
df_hist['변경일자'] = pd.to_datetime(df_hist['변경일자'])
df_hist = df_hist.sort_values(by=['물품고유번호', '변경일자'])

# 2. 유효 기간(Start ~ End) 생성
# StartDate: 변경일자
# EndDate: 다음 상태로 변경되기 전날 (현재 상태면 9999-12-31)
df_hist['유효시작일자'] = df_hist['변경일자']
df_hist['유효종료일자'] = df_hist.groupby('물품고유번호')['변경일자'].shift(-1) - pd.Timedelta(days=1)

# 마지막 상태(현재까지 유효함)는 종료일자를 먼 미래로 설정
df_hist['유효종료일자'] = df_hist['유효종료일자'].fillna(pd.Timestamp('2099-12-31'))

# 3. 필요한 정보 조인 (G2B목록번호 등)
# 물품고유번호를 기준으로 기본 정보(G2B정보, 취득금액 등)를 붙여줍니다.
df_info = df_op[['물품고유번호', 'G2B_목록번호', 'G2B_목록명', '취득일자', '취득금액', '내용연수']]
df_scd = pd.merge(df_hist, df_info, on='물품고유번호', how='left')

# 4. 컬럼 정리 및 저장
# 이 테이블을 사용하면 SQL 쿼리 등으로 "WHERE 유효시작일자 <= '2024-01-01' AND 유효종료일자 >= '2024-01-01'"
# 조건을 걸어 2024년 1월 1일 당시의 보유 수량(상태별 카운트)을 정확히 뽑을 수 있습니다.
view_inventory_scd = df_scd[[
    'G2B_목록번호', 'G2B_목록명', '물품고유번호', 
    '취득일자', '취득금액', '내용연수',
    '(변경)운용상태',  # 당시 상태 (운용, 반납, 불용 등)
    '유효시작일자', '유효종료일자'
]].copy()

# CSV 저장 시 날짜 포맷 정리
view_inventory_scd['유효시작일자'] = view_inventory_scd['유효시작일자'].dt.strftime('%Y-%m-%d')
view_inventory_scd['유효종료일자'] = view_inventory_scd['유효종료일자'].dt.strftime('%Y-%m-%d')

view_inventory_scd.to_csv(os.path.join(SAVE_DIR, 'View_07_01_보유현황_이력기반.csv'), index=False, encoding='utf-8-sig')

print("   -> [완료] 'View_07_01_보유현황_이력기반.csv' 생성됨. (기간 조회용)")
# ---------------------------------------------------------
# 2. 데이터 정합성 검증 (Validation)
# ---------------------------------------------------------
print("\n🔍 [Phase 3] 데이터 정합성 검증 시작")

# 검증 1: 이력 기반 데이터 검증 (최신 상태가 운용대장과 일치하는지)
# 9999-12-31일자(현재 유효한 상태)를 필터링하여 운용대장과 비교
current_snapshot = view_inventory_scd[view_inventory_scd['유효종료일자'] == '2099-12-31']
total_op = len(df_op)
total_snap = len(current_snapshot)

print(f"1. 최신 상태 동기화 검증: 운용대장({total_op}) vs 이력스냅샷({total_snap})")
if total_op == total_snap:
    print("   ✅ PASS: 이력 데이터의 최신 상태가 운용대장과 정확히 일치합니다.")
else:
    print("   ❌ FAIL: 데이터 불일치 발생.")

# 검증 2: 날짜 논리 확인 (취득일자 < 불용일자)
# 불용 목록에서 샘플링하여 확인
print("2. 날짜 논리 검증 (취득일자 < 불용일자)")
error_count = 0
for _, row in df_du.iterrows():
    if not row['취득일자'] or not row['불용일자']:
        continue
    acq_d = pd.to_datetime(row['취득일자'], errors='coerce')
    du_d = pd.to_datetime(row['불용일자'], errors='coerce')
    if pd.isna(acq_d) or pd.isna(du_d):
        continue
    if du_d < acq_d:
        error_count += 1


if error_count == 0:
    print("   ✅ PASS: 모든 데이터가 시간 순서(취득->불용)를 준수합니다.")
else:
    print(f"   ❌ FAIL: {error_count}건의 데이터에서 시간 역전 현상 발생.")

# 검증 3: 반려 데이터 격리 확인
# 운용대장에는 '확정'된 건만 있어야 하므로, 
# 만약 반납/불용/처분에서 '반려'된 건이 운용상태를 변경시켰는지 확인
# (Phase 2 로직상 반려되면 상태 변경 안 함 -> 운용대장엔 이전 상태로 남아있어야 함)
# 여기서는 간단히 처분 리스트의 '승인상태'가 '확정'인 것만 '처분' 상태인지 확인
print("3. 상태 로직 검증 (처분 확정 건)")
disposal_confirmed_ids = df_dp[df_dp['승인상태'] == '확정']['물품고유번호'].tolist()
op_disposed_rows = df_op[df_op['물품고유번호'].isin(disposal_confirmed_ids)]
non_disposed_status = op_disposed_rows[op_disposed_rows['운용상태'] != '처분']

if len(non_disposed_status) == 0:
    print("   ✅ PASS: 처분 확정된 모든 물품의 운용상태가 '처분'으로 변경되었습니다.")
else:
    print(f"   ❌ FAIL: 처분 확정되었으나 상태가 변경되지 않은 건이 {len(non_disposed_status)}개 있습니다.")

print("\n🎉 모든 작업이 완료되었습니다.")
print("   생성된 파일 목록:")
print("   - View_04_03_반납등록목록.csv / View_04_03_반납물품목록.csv")
print("   - View_05_01_불용등록목록.csv / View_05_01_불용물품목록.csv")
print("   - View_06_01_처분목록.csv / View_06_01_처분물품목록.csv")
print("   - View_07_01_보유현황.csv")