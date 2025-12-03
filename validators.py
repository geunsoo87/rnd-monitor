"""
데이터 검증 모듈
입력 데이터 검증 로직
"""
from datetime import datetime
from typing import Optional, Tuple, List
import pandas as pd


def validate_date(date_str: str) -> Tuple[bool, Optional[str]]:
    """날짜 형식 검증 (YYYY-MM-DD)"""
    if not date_str or not isinstance(date_str, str):
        return False, "날짜를 입력해주세요."
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, None
    except ValueError:
        return False, "날짜 형식이 올바르지 않습니다. (YYYY-MM-DD 형식)"


def validate_amount(amount: any) -> Tuple[bool, Optional[str], Optional[int]]:
    """금액 검증 (정수, 음수 가능)"""
    if amount is None:
        return False, "금액을 입력해주세요.", None
    
    # 문자열인 경우 숫자로 변환 시도
    if isinstance(amount, str):
        try:
            # 콤마 제거
            cleaned = amount.replace(",", "").replace(" ", "").replace("원", "")
            amount = int(float(cleaned))
        except ValueError:
            return False, "금액은 숫자여야 합니다.", None
    
    try:
        amount_int = int(amount)
        # 음수도 허용
        return True, None, amount_int
    except (ValueError, TypeError):
        return False, "금액은 숫자여야 합니다.", None


def validate_required_field(value: any, field_name: str) -> Tuple[bool, Optional[str]]:
    """필수 필드 검증"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return False, f"{field_name}은(는) 필수 입력 항목입니다."
    return True, None


def validate_expense_row(row: dict, erp_statistics: List[str], rcms_codes: List[str]) -> Tuple[bool, Optional[str]]:
    """지출내역 행 검증"""
    # 필수 필드 검증
    required_fields = {
        "통계목명": row.get("통계목명"),
        "사용일자": row.get("사용일자"),
        "지출결의명": row.get("지출결의명"),
        "지출결의액": row.get("지출결의액")
    }
    
    for field_name, value in required_fields.items():
        is_valid, error_msg = validate_required_field(value, field_name)
        if not is_valid:
            return False, error_msg
    
    # 통계목명 검증
    if row.get("통계목명") not in erp_statistics:
        return False, f"존재하지 않는 통계목명입니다: {row.get('통계목명')}"
    
    # 날짜 검증
    is_valid, error_msg = validate_date(row.get("사용일자"))
    if not is_valid:
        return False, error_msg
    
    # 금액 검증
    is_valid, error_msg, _ = validate_amount(row.get("지출결의액"))
    if not is_valid:
        return False, error_msg
    
    # RCMS 코드 검증 (선택 필드이지만 입력된 경우)
    rcms_code = row.get("rcms_code")
    if rcms_code and rcms_code not in rcms_codes:
        return False, f"존재하지 않는 RCMS 코드입니다: {rcms_code}"
    
    return True, None


def validate_budget_amount(amount: any) -> Tuple[bool, Optional[str], Optional[int]]:
    """예산 금액 검증"""
    return validate_amount(amount)

