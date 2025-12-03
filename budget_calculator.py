"""
예산 집계 계산 모듈
ERP 기준 및 RCMS 기준 집계 계산
"""
from typing import Dict, Tuple
import pandas as pd
import numpy as np


class BudgetCalculator:
    """예산 집계 계산 클래스"""
    
    @staticmethod
    def calculate_erp_budget(expense_df: pd.DataFrame, erp_budget_df: pd.DataFrame) -> pd.DataFrame:
        """ERP 기준 집계 계산"""
        result_df = erp_budget_df.copy()
        
        if expense_df.empty:
            # 지출내역이 없으면 집행액, 잔액, 집행률을 0으로 설정
            result_df['집행액'] = 0
            result_df['잔액'] = result_df['실행예산']
            result_df['집행률'] = 0.0
            return result_df
        
        # ERP는 모든 항목을 집계 (ERP는 무조건 정산된 것으로 봄)
        # 통계목명별 지출결의액 합계 ("총액" 제외)
        expense_summary = expense_df.groupby('통계목명')['지출결의액'].sum().reset_index()
        expense_summary.columns = ['통계목명', '집행액']
        
        # ERP_BUDGET과 조인 ("총액" 제외)
        result_df = result_df.merge(expense_summary, on='통계목명', how='left', suffixes=('', '_new'))
        
        # 집행액 업데이트 (없는 경우 0)
        result_df['집행액'] = result_df['집행액_new'].fillna(0).astype(int)
        result_df = result_df.drop(columns=['집행액_new'], errors='ignore')
        
        # "총액" 행은 다른 항목들의 합계로 계산
        total_row_idx = result_df[result_df['통계목명'] == '총액'].index
        if len(total_row_idx) > 0:
            # "총액"을 제외한 다른 항목들의 합계
            other_items = result_df[result_df['통계목명'] != '총액']
            total_executed = int(other_items['집행액'].sum())
            total_budget = int(other_items['실행예산'].sum())
            total_balance = total_budget - total_executed
            total_rate = (total_executed / total_budget * 100) if total_budget > 0 else 0.0
            
            # "총액" 행 업데이트
            result_df.loc[total_row_idx[0], '집행액'] = total_executed
            result_df.loc[total_row_idx[0], '실행예산'] = total_budget
            result_df.loc[total_row_idx[0], '잔액'] = total_balance
            result_df.loc[total_row_idx[0], '집행률'] = total_rate
        
        # 잔액 계산 (총액 제외한 항목들)
        other_items_mask = result_df['통계목명'] != '총액'
        result_df.loc[other_items_mask, '잔액'] = result_df.loc[other_items_mask, '실행예산'] - result_df.loc[other_items_mask, '집행액']
        
        # 집행률 계산 (실행예산이 0이 아닌 경우만, 총액 제외)
        mask = (result_df['실행예산'] > 0) & (result_df['통계목명'] != '총액')
        result_df.loc[mask, '집행률'] = (result_df.loc[mask, '집행액'] / result_df.loc[mask, '실행예산']) * 100
        result_df.loc[~mask & (result_df['통계목명'] != '총액'), '집행률'] = 0.0
        
        # updated_at 업데이트 (모든 행에 동일한 시간 설정)
        from datetime import datetime
        update_time = datetime.now()
        result_df['updated_at'] = update_time
        
        return result_df
    
    @staticmethod
    def calculate_rcms_budget(expense_df: pd.DataFrame, rcms_budget_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """RCMS 기준 집계 계산"""
        result_df = rcms_budget_df.copy()
        
        if expense_df.empty:
            # 지출내역이 없으면 모든 값을 0으로 설정
            result_df['used_amount'] = 0
            result_df['balance'] = result_df['budget_amount']
            result_df['rate'] = 0.0
            
            return result_df, {
                "미정산_금액": 0,
                "미정산_건수": 0,
                "미정산_ID_목록": []
            }
        
        # 정산 완료된 항목만 집계 (rcms_settled == True)
        # 데이터 타입 안전성을 위해 boolean으로 변환 후 비교
        expense_df = expense_df.copy()  # 원본 데이터 보호
        if 'rcms_settled' in expense_df.columns:
            # NaN, None, 문자열 등을 boolean으로 안전하게 변환
            # 먼저 문자열로 변환 후 boolean으로 변환 (더 안전)
            expense_df['rcms_settled'] = expense_df['rcms_settled'].fillna(False)
            # 숫자나 문자열도 처리
            expense_df['rcms_settled'] = expense_df['rcms_settled'].astype(str).str.lower().isin(['true', '1', 'yes', 'y', 't']).astype(bool)
        settled_expense_df = expense_df[expense_df['rcms_settled'] == True].copy()
        
        # rcms_code별 지출결의액 합계
        if settled_expense_df.empty:
            # 정산 완료된 항목이 없으면 모든 used_amount를 0으로 설정
            result_df['used_amount'] = 0
        else:
            expense_summary = settled_expense_df.groupby('rcms_code')['지출결의액'].sum().reset_index()
            expense_summary.columns = ['rcms_code', 'used_amount']
            
            # RCMS_BUDGET과 조인
            result_df = result_df.merge(expense_summary, on='rcms_code', how='left', suffixes=('', '_new'))
            
            # used_amount 업데이트 (없는 경우 0)
            result_df['used_amount'] = result_df['used_amount_new'].fillna(0).astype(int)
            result_df = result_df.drop(columns=['used_amount_new'], errors='ignore')
        
        # balance 계산
        result_df['balance'] = result_df['budget_amount'] - result_df['used_amount']
        
        # rate 계산 (budget_amount가 0이 아닌 경우만)
        mask = result_df['budget_amount'] > 0
        result_df.loc[mask, 'rate'] = (result_df.loc[mask, 'used_amount'] / result_df.loc[mask, 'budget_amount']) * 100
        result_df.loc[~mask, 'rate'] = 0.0
        
        # 미정산 금액 계산
        # expense_df는 이미 위에서 복사본으로 처리되었으므로 다시 복사할 필요 없음
        # 하지만 안전성을 위해 다시 확인
        if 'rcms_settled' in expense_df.columns:
            expense_df['rcms_settled'] = expense_df['rcms_settled'].fillna(False)
            expense_df['rcms_settled'] = expense_df['rcms_settled'].astype(str).str.lower().isin(['true', '1', 'yes', 'y', 't']).astype(bool)
        unsettled_df = expense_df[expense_df['rcms_settled'] == False]
        unsettled_amount = int(unsettled_df['지출결의액'].sum()) if not unsettled_df.empty else 0
        unsettled_count = len(unsettled_df)
        unsettled_ids = unsettled_df['id'].tolist() if not unsettled_df.empty and 'id' in unsettled_df.columns else []
        
        # updated_at 업데이트
        from datetime import datetime
        result_df['updated_at'] = datetime.now()
        
        return result_df, {
            "미정산_금액": unsettled_amount,
            "미정산_건수": unsettled_count,
            "미정산_ID_목록": unsettled_ids
        }
    
    @staticmethod
    def get_erp_summary(erp_budget_df: pd.DataFrame) -> Dict:
        """ERP 예산 요약 정보 (총액은 다른 항목들의 합계)"""
        if erp_budget_df.empty:
            return {
                "총_예산": 0,
                "총_집행액": 0,
                "총_잔액": 0,
                "총_집행률": 0.0
            }
        
        # "총액" 행을 찾아서 사용 (총액은 다른 항목들의 합계)
        total_row = erp_budget_df[erp_budget_df['통계목명'] == '총액']
        if not total_row.empty:
            total_budget = int(total_row['실행예산'].iloc[0])
            total_executed = int(total_row['집행액'].iloc[0])
            total_balance = int(total_row['잔액'].iloc[0])
        else:
            # "총액" 행이 없으면 다른 항목들의 합계
            other_items = erp_budget_df[erp_budget_df['통계목명'] != '총액']
            total_budget = int(other_items['실행예산'].sum())
            total_executed = int(other_items['집행액'].sum())
            total_balance = int(other_items['잔액'].sum())
        
        # 총 집행률 계산 (총 집행액 / 총 예산 * 100)
        total_rate = (total_executed / total_budget * 100) if total_budget > 0 else 0.0
        
        return {
            "총_예산": total_budget,
            "총_집행액": total_executed,
            "총_잔액": total_balance,
            "총_집행률": round(total_rate, 2)
        }

