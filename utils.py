"""
유틸리티 함수 모듈
날짜 포맷 변환, 금액 포맷 변환, 파일 경로 유틸리티 등
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
import os
import sys


def format_date(date_str: Optional[str] = None, date_obj: Optional[datetime] = None) -> str:
    """날짜를 YYYY-MM-DD 형식으로 변환"""
    if date_obj:
        return date_obj.strftime("%Y-%m-%d")
    elif date_str:
        try:
            # 다양한 형식 지원
            if isinstance(date_str, str):
                # YYYY-MM-DD 형식
                if len(date_str) == 10 and date_str.count('-') == 2:
                    return date_str
                # 다른 형식 시도
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def format_currency(amount: int) -> str:
    """금액을 한국어 형식으로 변환 (천 단위 구분)"""
    return f"{amount:,}원"


def format_number(num: int) -> str:
    """숫자를 천 단위 구분 형식으로 변환"""
    return f"{num:,}"


def parse_currency(amount_str: str) -> int:
    """문자열 금액을 정수로 변환 (콤마 제거)"""
    if isinstance(amount_str, (int, float)):
        return int(amount_str)
    if isinstance(amount_str, str):
        # 콤마와 공백 제거
        cleaned = amount_str.replace(",", "").replace(" ", "").replace("원", "")
        try:
            return int(float(cleaned))
        except ValueError:
            return 0
    return 0


def get_file_path(folder_path: str, filename: str = "master.xlsx") -> Path:
    """파일 경로 생성"""
    return Path(folder_path) / filename

def get_master_filename(folder_path: str) -> str:
    """폴더명을 기반으로 master 파일명 생성"""
    folder_name = Path(folder_path).name
    if folder_name:
        # 폴더명에서 파일명으로 사용할 수 없는 문자 제거
        safe_name = folder_name.replace("\\", "_").replace("/", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
        return f"{safe_name}_master.xlsx"
    return "master.xlsx"


def ensure_folder_exists(folder_path: str) -> bool:
    """폴더가 없으면 생성"""
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def open_folder_in_explorer(folder_path: str) -> bool:
    """파일 탐색기에서 폴더 열기"""
    try:
        folder_path = os.path.abspath(folder_path)
        if os.name == 'nt':  # Windows
            os.startfile(folder_path)
        elif os.name == 'posix':  # macOS, Linux
            os.system(f'open "{folder_path}"' if sys.platform == 'darwin' else f'xdg-open "{folder_path}"')
        return True
    except Exception as e:
        print(f"폴더 열기 오류: {e}")
        return False


def get_backup_filename(base_filename: str = "master.xlsx") -> str:
    """백업 파일명 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(base_filename).stem
    return f"{base_name}_backup_{timestamp}.xlsx"

