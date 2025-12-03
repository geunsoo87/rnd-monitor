"""
데이터 로드/저장 관리 모듈
master.xlsx 파일 읽기/쓰기, 백업 관리
"""
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
import pandas as pd
from openpyxl import load_workbook
import shutil

from initial_data import (
    create_expense_df, create_erp_budget_df, 
    create_rcms_budget_df, create_mapping_df
)
from utils import get_backup_filename, ensure_folder_exists


class DataManager:
    """데이터 파일 관리 클래스"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.folder_path = self.file_path.parent
    
    def file_exists(self) -> bool:
        """파일 존재 여부 확인"""
        return self.file_path.exists()
    
    def create_initial_file(self) -> bool:
        """초기 master.xlsx 파일 생성"""
        try:
            # 폴더 생성
            ensure_folder_exists(str(self.folder_path))
            
            # 각 시트의 초기 DataFrame 생성
            expense_df = create_expense_df()
            erp_budget_df = create_erp_budget_df()
            rcms_budget_df = create_rcms_budget_df()
            mapping_df = create_mapping_df()
            
            # 엑셀 파일로 저장
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                expense_df.to_excel(writer, sheet_name='EXPENSE', index=False)
                erp_budget_df.to_excel(writer, sheet_name='ERP_BUDGET', index=False)
                rcms_budget_df.to_excel(writer, sheet_name='RCMS_BUDGET', index=False)
                mapping_df.to_excel(writer, sheet_name='MAPPING_ERP_RCMS', index=False)
            
            return True
        except Exception as e:
            print(f"초기 파일 생성 오류: {e}")
            return False
    
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """모든 시트 로드"""
        if not self.file_exists():
            return {}
        
        try:
            data = {}
            excel_file = pd.ExcelFile(self.file_path)
            
            # 각 시트 읽기
            sheet_names = ['EXPENSE', 'ERP_BUDGET', 'RCMS_BUDGET', 'MAPPING_ERP_RCMS']
            for sheet_name in sheet_names:
                if sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # EXPENSE 시트의 경우 rcms_settled 컬럼을 boolean으로 변환
                    if sheet_name == 'EXPENSE' and 'rcms_settled' in df.columns:
                        # Excel에서 불러온 값이 문자열, 숫자, NaN 등일 수 있으므로 안전하게 변환
                        df['rcms_settled'] = df['rcms_settled'].fillna(False)
                        # 문자열 'True', 'False', 숫자 1, 0 등을 boolean으로 변환
                        df['rcms_settled'] = df['rcms_settled'].astype(str).str.lower().isin(['true', '1', 'yes', 'y', 't']).astype(bool)
                    
                    data[sheet_name] = df
                else:
                    # 시트가 없으면 빈 DataFrame 생성
                    if sheet_name == 'EXPENSE':
                        data[sheet_name] = create_expense_df()
                    elif sheet_name == 'ERP_BUDGET':
                        data[sheet_name] = create_erp_budget_df()
                    elif sheet_name == 'RCMS_BUDGET':
                        data[sheet_name] = create_rcms_budget_df()
                    elif sheet_name == 'MAPPING_ERP_RCMS':
                        data[sheet_name] = create_mapping_df()
            
            return data
        except Exception as e:
            print(f"파일 로드 오류: {e}")
            return {}
    
    def save_all(self, data: Dict[str, pd.DataFrame]) -> Tuple[bool, Optional[str]]:
        """모든 시트 저장"""
        try:
            # 백업 생성 (파일이 존재하는 경우에만)
            if self.file_exists():
                backup_path = self._create_backup()
                if not backup_path:
                    # 백업 실패해도 저장은 진행 (경고만)
                    print("경고: 백업 생성에 실패했지만 저장은 진행합니다.")
            
            # 폴더 생성
            ensure_folder_exists(str(self.folder_path))
            
            # 엑셀 파일로 저장
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                for sheet_name, df in data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return True, None
        except Exception as e:
            error_msg = f"파일 저장 오류: {e}"
            print(error_msg)
            return False, error_msg
    
    def _create_backup(self) -> Optional[Path]:
        """백업 파일 생성 (최종 저장 시 자동 생성)"""
        if not self.file_exists():
            return None
        
        try:
            backup_filename = get_backup_filename(self.file_path.name)
            backup_path = self.folder_path / backup_filename
            shutil.copy2(self.file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"백업 생성 오류: {e}")
            return None
    
    def get_file_info(self) -> Dict[str, str]:
        """파일 정보 반환"""
        if not self.file_exists():
            return {
                "exists": False,
                "path": str(self.file_path),
                "folder": str(self.folder_path)
            }
        
        stat = self.file_path.stat()
        return {
            "exists": True,
            "path": str(self.file_path),
            "folder": str(self.folder_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }

