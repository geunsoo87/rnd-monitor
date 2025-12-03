"""
초기 데이터 생성 모듈
ERP 통계목 및 RCMS 세부항목 초기 데이터 생성
"""
from datetime import datetime
from typing import Optional
import pandas as pd


def get_erp_statistics_list() -> list:
    """ERP 통계목 목록 반환 (14개)"""
    return [
        "총액",
        "기타직보수",
        "상용임금",
        "일반수용비",
        "임차료",
        "유류비",
        "재료비",
        "국내여비",
        "국외업무여비",
        "사업추진비",
        "자산취득비",
        "무형자산",
        "일반관리비",
        "고용부담금"
    ]


def get_rcms_items_list() -> list:
    """RCMS 세부항목 목록 반환 (23개)"""
    return [
        # 인건비 (2개)
        {"rcms_name": "연구근접지원인건비", "parent_category": "인건비", "rcms_code": "RCMS_001"},
        {"rcms_name": "참여연구원인건비", "parent_category": "인건비", "rcms_code": "RCMS_002"},
        
        # 연구시설장비비 (4개)
        {"rcms_name": "연구시설장비임차비", "parent_category": "연구시설장비비", "rcms_code": "RCMS_003"},
        {"rcms_name": "연구시설장비구입설치비", "parent_category": "연구시설장비비", "rcms_code": "RCMS_004"},
        {"rcms_name": "연구시설장비운영유지비", "parent_category": "연구시설장비비", "rcms_code": "RCMS_005"},
        {"rcms_name": "연구인프라조성비", "parent_category": "연구시설장비비", "rcms_code": "RCMS_006"},
        
        # 연구재료비 (3개)
        {"rcms_name": "연구개발과제관리비", "parent_category": "연구재료비", "rcms_code": "RCMS_007"},
        {"rcms_name": "연구재료구입비", "parent_category": "연구재료비", "rcms_code": "RCMS_008"},
        {"rcms_name": "연구재료제작비", "parent_category": "연구재료비", "rcms_code": "RCMS_009"},
        
        # 연구활동비 (12개)
        {"rcms_name": "소프트웨어활용비", "parent_category": "연구활동비", "rcms_code": "RCMS_010"},
        {"rcms_name": "연구실운영비", "parent_category": "연구활동비", "rcms_code": "RCMS_011"},
        {"rcms_name": "연구인력지원비", "parent_category": "연구활동비", "rcms_code": "RCMS_012"},
        {"rcms_name": "연구활동비기타비용", "parent_category": "연구활동비", "rcms_code": "RCMS_013"},
        {"rcms_name": "외부전문기술활용비", "parent_category": "연구활동비", "rcms_code": "RCMS_014"},
        {"rcms_name": "종합사업관리비", "parent_category": "연구활동비", "rcms_code": "RCMS_015"},
        {"rcms_name": "지식재산창출활동비", "parent_category": "연구활동비", "rcms_code": "RCMS_016"},
        {"rcms_name": "출장비", "parent_category": "연구활동비", "rcms_code": "RCMS_017"},
        {"rcms_name": "클라우드컴퓨팅서비스활용비", "parent_category": "연구활동비", "rcms_code": "RCMS_018"},
        {"rcms_name": "해외연구자유치지원비", "parent_category": "연구활동비", "rcms_code": "RCMS_019"},
        {"rcms_name": "회의비", "parent_category": "연구활동비", "rcms_code": "RCMS_020"},
        
        # 연구수당 (1개)
        {"rcms_name": "연구수당", "parent_category": "연구수당", "rcms_code": "RCMS_021"},
        
        # 간접비 (1개)
        {"rcms_name": "간접비", "parent_category": "간접비", "rcms_code": "RCMS_022"},
    ]


def create_erp_budget_df() -> pd.DataFrame:
    """ERP_BUDGET 초기 DataFrame 생성"""
    statistics_list = get_erp_statistics_list()
    now = datetime.now()
    
    data = {
        "통계목명": statistics_list,
        "실행예산": [0] * len(statistics_list),
        "집행액": [0] * len(statistics_list),
        "잔액": [0] * len(statistics_list),
        "집행률": [0.0] * len(statistics_list),
        "updated_at": [now] * len(statistics_list)
    }
    
    return pd.DataFrame(data)


def create_rcms_budget_df() -> pd.DataFrame:
    """RCMS_BUDGET 초기 DataFrame 생성"""
    items_list = get_rcms_items_list()
    now = datetime.now()
    
    data = {
        "rcms_code": [item["rcms_code"] for item in items_list],
        "rcms_name": [item["rcms_name"] for item in items_list],
        "parent_category": [item["parent_category"] for item in items_list],
        "budget_amount": [0] * len(items_list),
        "used_amount": [0] * len(items_list),
        "balance": [0] * len(items_list),
        "rate": [0.0] * len(items_list),
        "updated_at": [now] * len(items_list)
    }
    
    return pd.DataFrame(data)


def create_expense_df() -> pd.DataFrame:
    """EXPENSE 초기 DataFrame 생성 (헤더만)"""
    columns = [
        "id", "통계목명", "사용일자", "지출결의명", "상세내역",
        "지출결의액", "rcms_code", "rcms_name", "rcms_settled",
        "created_at", "updated_at"
    ]
    return pd.DataFrame(columns=columns)


def create_mapping_df() -> pd.DataFrame:
    """MAPPING_ERP_RCMS 초기 DataFrame 생성 (빈 구조)"""
    columns = ["ERP_통계목명", "rcms_code", "rcms_name", "priority"]
    return pd.DataFrame(columns=columns)


def get_rcms_code_by_name(rcms_name: str) -> Optional[str]:
    """RCMS 항목명으로 코드 찾기"""
    items_list = get_rcms_items_list()
    for item in items_list:
        if item["rcms_name"] == rcms_name:
            return item["rcms_code"]
    return None


def get_rcms_name_by_code(rcms_code: str):
    """RCMS 코드로 항목명 찾기"""
    items_list = get_rcms_items_list()
    for item in items_list:
        if item["rcms_code"] == rcms_code:
            return item["rcms_name"]
    return None

