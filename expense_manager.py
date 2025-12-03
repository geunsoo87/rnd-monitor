"""
지출내역 관리 모듈
지출내역 CRUD 작업, 필터링, 검색
"""
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import pandas as pd

from initial_data import get_rcms_code_by_name, get_rcms_name_by_code
from validators import validate_expense_row


class ExpenseManager:
    """지출내역 관리 클래스"""
    
    def __init__(self, expense_df: pd.DataFrame):
        self.df = expense_df.copy() if not expense_df.empty else self._create_empty_df()
        # id 자동 증가를 위한 최대값 추적
        if not self.df.empty and 'id' in self.df.columns:
            self._max_id = self.df['id'].max() if pd.notna(self.df['id'].max()) else 0
        else:
            self._max_id = 0
    
    def _create_empty_df(self) -> pd.DataFrame:
        """빈 DataFrame 생성"""
        columns = [
            "id", "통계목명", "사용일자", "지출결의명", "상세내역",
            "지출결의액", "rcms_code", "rcms_name", "rcms_settled",
            "created_at", "updated_at"
        ]
        return pd.DataFrame(columns=columns)
    
    def add_row(self, row_data: Dict) -> Tuple[bool, Optional[str]]:
        """새 행 추가"""
        # id 자동 할당
        self._max_id += 1
        row_data['id'] = self._max_id
        
        # 타임스탬프 추가
        now = datetime.now()
        row_data['created_at'] = now
        row_data['updated_at'] = now
        
        # rcms_code가 있으면 rcms_name 자동 채움
        if row_data.get('rcms_code') and not row_data.get('rcms_name'):
            rcms_name = get_rcms_name_by_code(row_data['rcms_code'])
            if rcms_name:
                row_data['rcms_name'] = rcms_name
        
        # rcms_settled 기본값
        if 'rcms_settled' not in row_data or row_data['rcms_settled'] is None:
            row_data['rcms_settled'] = False
        
        # DataFrame에 추가
        new_row = pd.DataFrame([row_data])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        
        return True, None
    
    def update_row(self, row_id: int, row_data: Dict) -> Tuple[bool, Optional[str]]:
        """행 수정"""
        idx = self.df[self.df['id'] == row_id].index
        if len(idx) == 0:
            return False, f"ID {row_id}에 해당하는 행을 찾을 수 없습니다."
        
        # id는 변경하지 않음
        row_data.pop('id', None)
        
        # updated_at 업데이트
        row_data['updated_at'] = datetime.now()
        
        # rcms_code가 변경되면 rcms_name 자동 업데이트
        if 'rcms_code' in row_data and row_data['rcms_code']:
            rcms_name = get_rcms_name_by_code(row_data['rcms_code'])
            if rcms_name:
                row_data['rcms_name'] = rcms_name
        
        # 데이터 업데이트
        for key, value in row_data.items():
            self.df.at[idx[0], key] = value
        
        return True, None
    
    def delete_row(self, row_id: int) -> Tuple[bool, Optional[str]]:
        """행 삭제"""
        idx = self.df[self.df['id'] == row_id].index
        if len(idx) == 0:
            return False, f"ID {row_id}에 해당하는 행을 찾을 수 없습니다."
        
        self.df = self.df.drop(idx).reset_index(drop=True)
        return True, None
    
    def delete_rows(self, row_ids: List[int]) -> Tuple[bool, Optional[str]]:
        """여러 행 삭제"""
        self.df = self.df[~self.df['id'].isin(row_ids)].reset_index(drop=True)
        return True, None
    
    def get_all(self) -> pd.DataFrame:
        """모든 데이터 반환"""
        return self.df.copy()
    
    def get_by_id(self, row_id: int) -> Optional[pd.Series]:
        """ID로 행 조회"""
        result = self.df[self.df['id'] == row_id]
        return result.iloc[0] if len(result) > 0 else None
    
    def filter(self, filters: Dict) -> pd.DataFrame:
        """필터링"""
        filtered_df = self.df.copy()
        
        # 통계목명 필터
        if '통계목명' in filters and filters['통계목명']:
            filtered_df = filtered_df[filtered_df['통계목명'] == filters['통계목명']]
        
        # 날짜 범위 필터
        if '시작일' in filters and filters['시작일']:
            filtered_df = filtered_df[filtered_df['사용일자'] >= filters['시작일']]
        if '종료일' in filters and filters['종료일']:
            filtered_df = filtered_df[filtered_df['사용일자'] <= filters['종료일']]
        
        # 지출결의명 검색
        if '지출결의명' in filters and filters['지출결의명']:
            keyword = str(filters['지출결의명']).strip().lower()
            if keyword:
                # 문자열 타입으로 변환 후 검색 (정규식 사용 안 함)
                filtered_df = filtered_df[
                    filtered_df['지출결의명'].astype(str).str.lower().str.contains(keyword, na=False, regex=False)
                ]
        
        # RCMS 정산 상태 필터
        if 'rcms_settled' in filters and filters['rcms_settled'] is not None:
            filtered_df = filtered_df[filtered_df['rcms_settled'] == filters['rcms_settled']]
        
        # 금액 범위 필터
        if '최소금액' in filters and filters['최소금액'] is not None:
            filtered_df = filtered_df[filtered_df['지출결의액'] >= filters['최소금액']]
        if '최대금액' in filters and filters['최대금액'] is not None:
            filtered_df = filtered_df[filtered_df['지출결의액'] <= filters['최대금액']]
        
        return filtered_df
    
    def get_summary(self) -> Dict:
        """요약 정보 반환"""
        if self.df.empty:
            return {
                "총_행수": 0,
                "총_금액": 0
            }
        
        total_amount = self.df['지출결의액'].sum() if '지출결의액' in self.df.columns else 0
        return {
            "총_행수": len(self.df),
            "총_금액": int(total_amount) if pd.notna(total_amount) else 0
        }

