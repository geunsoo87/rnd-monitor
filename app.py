"""
연구비 예산관리 시스템 - Streamlit 메인 애플리케이션
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import os

from config import config_manager
from data_manager import DataManager
from expense_manager import ExpenseManager
from budget_calculator import BudgetCalculator
from initial_data import get_erp_statistics_list, get_rcms_items_list
from utils import get_file_path, ensure_folder_exists, open_folder_in_explorer, format_currency, get_master_filename
from ui_components import (
    display_file_info, display_expense_table, display_erp_budget_table,
    display_rcms_budget_table, plot_erp_budget_chart, plot_rcms_budget_chart, show_summary_cards
)
from folder_dialog import select_folder

# 페이지 설정
st.set_page_config(
    page_title="연구비 예산관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = None
if 'expense_manager' not in st.session_state:
    st.session_state.expense_manager = None
if 'erp_budget_df' not in st.session_state:
    st.session_state.erp_budget_df = pd.DataFrame()
if 'rcms_budget_df' not in st.session_state:
    st.session_state.rcms_budget_df = pd.DataFrame()
if 'mapping_df' not in st.session_state:
    st.session_state.mapping_df = pd.DataFrame()
if 'current_file_path' not in st.session_state:
    st.session_state.current_file_path = None
if 'page' not in st.session_state:
    st.session_state.page = 'file_select'


def has_data_changes(new_rows: list, updated_rows: list, deleted_ids: set,
                     original_expense_df: pd.DataFrame, current_expense_df: pd.DataFrame,
                     original_erp_budget: pd.DataFrame, current_erp_budget: pd.DataFrame,
                     original_rcms_budget: pd.DataFrame, current_rcms_budget: pd.DataFrame) -> bool:
    """변경사항이 있는지 확인"""
    # 지출내역 변경 확인
    if new_rows or updated_rows or deleted_ids:
        return True
    
    # ERP 예산 변경 확인 (실행예산만 비교, 집계 결과는 제외)
    if not original_erp_budget.empty and not current_erp_budget.empty:
        original_budget = original_erp_budget[['통계목명', '실행예산']].sort_values('통계목명').reset_index(drop=True)
        current_budget = current_erp_budget[['통계목명', '실행예산']].sort_values('통계목명').reset_index(drop=True)
        if not original_budget.equals(current_budget):
            return True
    
    # RCMS 예산 변경 확인 (budget_amount만 비교, 집계 결과는 제외)
    if not original_rcms_budget.empty and not current_rcms_budget.empty:
        original_rcms = original_rcms_budget[['rcms_code', 'rcms_name', 'budget_amount']].sort_values('rcms_code').reset_index(drop=True)
        current_rcms = current_rcms_budget[['rcms_code', 'rcms_name', 'budget_amount']].sort_values('rcms_code').reset_index(drop=True)
        if not original_rcms.equals(current_rcms):
            return True
    
    return False


def load_data(file_path: str):
    """데이터 로드"""
    try:
        data_manager = DataManager(file_path)
        
        # 파일이 없으면 생성
        if not data_manager.file_exists():
            if not data_manager.create_initial_file():
                st.error("초기 파일 생성에 실패했습니다.")
                return False
        
        # 데이터 로드
        data = data_manager.load_all()
        
        if not data:
            st.error("데이터 로드에 실패했습니다.")
            return False
        
        # 세션 상태에 저장
        st.session_state.data_manager = data_manager
        st.session_state.expense_manager = ExpenseManager(data.get('EXPENSE', pd.DataFrame()))
        st.session_state.erp_budget_df = data.get('ERP_BUDGET', pd.DataFrame())
        st.session_state.rcms_budget_df = data.get('RCMS_BUDGET', pd.DataFrame())
        st.session_state.mapping_df = data.get('MAPPING_ERP_RCMS', pd.DataFrame())
        st.session_state.current_file_path = file_path
        
        # last_work_folder 업데이트
        config_manager.update_last_work_folder(str(Path(file_path).parent))
        
        return True
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return False


def save_data():
    """데이터 저장"""
    if not st.session_state.data_manager:
        st.error("파일이 선택되지 않았습니다.")
        return False
    
    try:
        data = {
            'EXPENSE': st.session_state.expense_manager.get_all(),
            'ERP_BUDGET': st.session_state.erp_budget_df,
            'RCMS_BUDGET': st.session_state.rcms_budget_df,
            'MAPPING_ERP_RCMS': st.session_state.mapping_df
        }
        
        success, error_msg = st.session_state.data_manager.save_all(data)
        if success:
            st.success("저장되었습니다.")
            return True
        else:
            st.error(f"저장 실패: {error_msg}")
            return False
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False


def show_file_select_page():
    """파일 선택 페이지"""
    st.title("📊 연구비 예산관리 시스템")
    st.markdown("---")
    
    st.header("작업 파일 선택")
    
    # 최근 사용한 폴더
    last_folder = config_manager.get("last_work_folder", "")
    if last_folder:
        st.subheader("최근 사용한 폴더")
        if st.button(f"📁 {last_folder}", key="last_folder_btn"):
            # 기존 master.xlsx가 있으면 사용, 없으면 폴더명 기반 파일명 사용
            master_file = get_master_filename(last_folder)
            file_path = get_file_path(last_folder, master_file)
            # 기존 master.xlsx도 확인
            if not file_path.exists():
                old_master = get_file_path(last_folder, "master.xlsx")
                if old_master.exists():
                    file_path = old_master
            if load_data(str(file_path)):
                st.session_state.page = 'main'
                st.rerun()
    
    st.markdown("---")
    
    # 파일 선택 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("기존 파일 열기")
        st.write("master.xlsx 파일을 직접 선택합니다.")
        uploaded_file = st.file_uploader("파일 선택", type=['xlsx'], key="file_upload")
        if uploaded_file:
            # 임시 파일로 저장 후 로드
            temp_path = Path("temp") / uploaded_file.name
            ensure_folder_exists("temp")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            if load_data(str(temp_path)):
                st.session_state.page = 'main'
                st.rerun()
    
    with col2:
        st.subheader("폴더 선택")
        st.write("작업 폴더를 선택하면 해당 폴더의 master.xlsx를 사용합니다. (파일이 없으면 자동 생성)")
        
        # 세션 상태 초기화 (한 번만, 위젯 생성 전)
        if 'folder_input' not in st.session_state:
            st.session_state.folder_input = config_manager.get("last_work_folder", "")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            # Streamlit Cloud에서는 tkinter가 작동하지 않으므로 조건부로 표시
            try:
                if st.button("📁 폴더 찾아보기", key="browse_folder_btn"):
                    selected = select_folder(config_manager.get("last_work_folder", ""))
                    if selected:
                        # 세션 상태 업데이트 (위젯 생성 전)
                        st.session_state.folder_input = selected
                        st.rerun()
            except Exception as e:
                # Streamlit Cloud 환경에서는 폴더 찾아보기 버튼 숨김
                st.caption("💡 **참고**: Streamlit Cloud 환경에서는 폴더 찾아보기 기능을 사용할 수 없습니다. 폴더 경로를 직접 입력하거나 파일 업로드를 사용하세요.")
        
        # 폴더 경로 입력 (세션 상태와 동기화)
        folder_path = st.text_input("폴더 경로", key="folder_input", value=st.session_state.folder_input)
        
        with col_btn2:
            if st.button("폴더에서 열기", key="folder_open_btn"):
                # 위젯에서 가져온 값 사용
                folder = folder_path.strip() if folder_path else ""
                
                if folder:
                    # 폴더가 없으면 생성
                    ensure_folder_exists(folder)
                    # 폴더명 기반 파일명 생성
                    master_file = get_master_filename(folder)
                    file_path = get_file_path(folder, master_file)
                    # 기존 master.xlsx가 있으면 사용 (호환성)
                    old_master = get_file_path(folder, "master.xlsx")
                    if old_master.exists() and not file_path.exists():
                        file_path = old_master
                    # 파일이 없으면 자동 생성 (load_data 내부에서 처리)
                    if load_data(str(file_path)):
                        st.session_state.page = 'main'
                        st.rerun()
                else:
                    st.error("폴더 경로를 입력하거나 선택해주세요.")


def show_main_page():
    """메인 페이지"""
    # 헤더
    st.title("📊 연구비 예산관리 시스템")
    
    # 파일 정보
    if st.session_state.current_file_path:
        file_path = Path(st.session_state.current_file_path)
        folder_path = file_path.parent
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            display_file_info(str(file_path), str(folder_path))
        with col2:
            if st.button("🔄 파일 변경", key="change_file_btn"):
                st.session_state.page = 'file_select'
                st.rerun()
        with col3:
            if st.button("📂 폴더 열기", key="open_folder_btn"):
                open_folder_in_explorer(str(folder_path))
    
    st.markdown("---")
    
    # 메뉴
    menu = st.radio(
        "메뉴 선택",
        ["지출내역 관리", "집행 결과"],
        horizontal=True,
        key="main_menu"
    )
    
    st.markdown("---")
    
    # 페이지 라우팅
    if menu == "지출내역 관리":
        show_expense_page()
    elif menu == "집행 결과":
        show_execution_result_page()


def show_expense_page():
    """지출내역 관리 페이지"""
    st.header("💰 지출내역 관리")
    
    if not st.session_state.expense_manager:
        st.warning("파일을 먼저 선택해주세요.")
        return
    
    expense_manager = st.session_state.expense_manager
    
    # 검색/필터
    with st.expander("🔍 검색/필터", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            erp_statistics = get_erp_statistics_list()
            selected_stat = st.selectbox("통계목명", [""] + erp_statistics, key="filter_stat")
            start_date = st.date_input("시작일", key="filter_start_date")
            end_date = st.date_input("종료일", key="filter_end_date")
        with col2:
            search_keyword = st.text_input("지출결의명 검색", key="filter_keyword")
            settled_filter = st.selectbox("RCMS 정산 여부", ["전체", "정산 완료", "미정산"], key="filter_settled")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("검색", key="search_btn"):
                st.session_state.filter_applied = True
        with col_btn2:
            if st.button("초기화", key="reset_btn"):
                st.session_state.filter_applied = False
    
    # 필터링 적용
    if st.session_state.get('filter_applied', False):
        filters = {}
        if selected_stat:
            filters['통계목명'] = selected_stat
        if start_date:
            filters['시작일'] = start_date.strftime("%Y-%m-%d")
        if end_date:
            filters['종료일'] = end_date.strftime("%Y-%m-%d")
        if search_keyword:
            filters['지출결의명'] = search_keyword
        if settled_filter == "정산 완료":
            filters['rcms_settled'] = True
        elif settled_filter == "미정산":
            filters['rcms_settled'] = False
        
        filtered_df = expense_manager.filter(filters)
    else:
        filtered_df = expense_manager.get_all()
    
    # 데이터 테이블 - 직접 편집 가능
    st.subheader("지출내역 (표에서 직접 입력/수정 가능)")
    st.caption("💡 **안내**: 표에서 직접 데이터를 입력/수정할 수 있습니다. ID는 자동으로 할당됩니다. 금액은 숫자만 입력하세요 (예: 1000000).")
    
    # 편집 가능한 컬럼만 선택 (rcms_code는 숨기고 rcms_name만 표시, ID는 표시만)
    editable_columns = ['통계목명', '사용일자', '지출결의명', '상세내역', '지출결의액', 'rcms_name', 'rcms_settled']
    display_columns = ['id'] + editable_columns
    
    # RCMS 옵션 준비
    rcms_items = get_rcms_items_list()
    rcms_name_options = [""] + [item['rcms_name'] for item in rcms_items]
    
    # ID 자동 증가를 위한 최대값 계산
    if not filtered_df.empty and 'id' in filtered_df.columns:
        max_id = int(filtered_df['id'].max()) if pd.notna(filtered_df['id'].max()) else 0
    else:
        max_id = 0
    
    # expense_manager에서도 최대 ID 가져오기 (더 정확함)
    if st.session_state.expense_manager:
        expense_all = st.session_state.expense_manager.get_all()
        if not expense_all.empty and 'id' in expense_all.columns:
            manager_max_id = int(expense_all['id'].max()) if pd.notna(expense_all['id'].max()) else 0
            max_id = max(max_id, manager_max_id)
    
    # 기존 데이터가 있으면 표시, 없으면 빈 DataFrame 생성
    if filtered_df.empty:
        # 빈 DataFrame 생성 (새 행 추가를 위해)
        empty_df = pd.DataFrame(columns=display_columns)
        edited_df = st.data_editor(
            empty_df,
            use_container_width=True,
            num_rows="dynamic",
            key="expense_editor",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, help="자동 할당됩니다"),
                "통계목명": st.column_config.SelectboxColumn("통계목명", options=get_erp_statistics_list(), required=True),
                "사용일자": st.column_config.DateColumn("사용일자", required=True),
                "지출결의명": st.column_config.TextColumn("지출결의명", required=True),
                "상세내역": st.column_config.TextColumn("상세내역"),
                "지출결의액": st.column_config.NumberColumn("지출결의액", step=1000, format="%d", required=True, help="숫자만 입력 (예: 1000000, 음수 가능)"),
                "rcms_name": st.column_config.SelectboxColumn("RCMS 항목", options=rcms_name_options),
                "rcms_settled": st.column_config.CheckboxColumn("RCMS 정산 여부")
            }
        )
    else:
        # 기존 데이터 표시 및 편집
        display_df = filtered_df[display_columns].copy()
        # 날짜 형식 변환 (문자열을 날짜로)
        if '사용일자' in display_df.columns:
            display_df['사용일자'] = pd.to_datetime(display_df['사용일자'], errors='coerce')
        
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            key="expense_editor",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, help="자동 할당됩니다"),
                "통계목명": st.column_config.SelectboxColumn("통계목명", options=get_erp_statistics_list(), required=True),
                "사용일자": st.column_config.DateColumn("사용일자", required=True),
                "지출결의명": st.column_config.TextColumn("지출결의명", required=True),
                "상세내역": st.column_config.TextColumn("상세내역"),
                "지출결의액": st.column_config.NumberColumn(
                    "지출결의액", 
                    step=1000, 
                    format="%d", 
                    required=True, 
                    help="숫자만 입력하세요 (예: 1000000, 음수 가능). 천단위 구분 쉼표는 자동으로 표시됩니다."
                ),
                "rcms_name": st.column_config.SelectboxColumn("RCMS 항목", options=rcms_name_options),
                "rcms_settled": st.column_config.CheckboxColumn("RCMS 정산 여부")
            },
            on_change=None
        )
        
        # 지출결의액을 천단위 구분 쉼표로 표시 (참고용)
        if not edited_df.empty and '지출결의액' in edited_df.columns:
            st.caption("💡 **참고**: 지출결의액은 천단위 구분 쉼표로 표시됩니다. 편집 시에는 숫자만 입력하세요.")
    
    
    # 편집된 데이터를 세션에 저장 (저장 버튼을 눌러야 반영됨)
    st.session_state.edited_expense_df = edited_df
    st.session_state.max_id_for_new_rows = max_id
    
    # 요약 정보
    summary = expense_manager.get_summary()
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("총 행 수", summary['총_행수'])
    with col2:
        st.metric("총 금액", format_currency(summary['총_금액']))
    
    # 반영저장 버튼
    st.markdown("---")
    if st.button("💾 반영저장", key="save_expense_btn", type="primary", use_container_width=True):
        # 지출내역 저장 및 ERP/RCMS 집계 자동 실행
        if 'edited_expense_df' in st.session_state and st.session_state.expense_manager:
            edited_df = st.session_state.edited_expense_df
            expense_manager = st.session_state.expense_manager
            current_df = expense_manager.get_all()
            
            if not current_df.empty:
                existing_ids = set(current_df['id'].astype(int))
            else:
                existing_ids = set()
            
            new_rows = []
            updated_rows = []
            deleted_ids = set()  # 삭제된 ID 초기화
            
            # ID 자동 할당을 위한 최대값 가져오기
            if 'max_id_for_new_rows' in st.session_state:
                current_max_id = st.session_state.max_id_for_new_rows
            else:
                if not current_df.empty and 'id' in current_df.columns:
                    current_max_id = int(current_df['id'].max()) if pd.notna(current_df['id'].max()) else 0
                else:
                    current_max_id = 0
            
            for idx, row in edited_df.iterrows():
                if pd.isna(row.get('통계목명')) or pd.isna(row.get('사용일자')) or pd.isna(row.get('지출결의명')) or pd.isna(row.get('지출결의액')):
                    continue
                
                # ID 처리: 없거나 0이면 자동 할당
                row_id = None
                if pd.notna(row.get('id')) and str(row['id']).strip() != '':
                    try:
                        row_id_val = int(float(row['id']))
                        if row_id_val > 0:
                            row_id = row_id_val
                    except (ValueError, TypeError):
                        row_id = None
                
                # ID가 없거나 0이면 자동 할당
                if row_id is None or row_id == 0:
                    current_max_id += 1
                    row_id = current_max_id
                
                use_date = row['사용일자']
                if isinstance(use_date, str):
                    from datetime import datetime
                    try:
                        use_date = datetime.strptime(use_date, "%Y-%m-%d")
                    except:
                        use_date = pd.to_datetime(use_date, errors='coerce')
                date_str = use_date.strftime("%Y-%m-%d") if hasattr(use_date, 'strftime') else str(use_date)
                
                # rcms_name만 표시되므로, rcms_name을 선택하면 rcms_code 자동 매핑
                rcms_name = str(row['rcms_name']).strip() if pd.notna(row['rcms_name']) else ""
                rcms_code = ""
                
                # rcms_name이 있으면 rcms_code 자동 찾기
                if rcms_name:
                    for item in get_rcms_items_list():
                        if item['rcms_name'] == rcms_name:
                            rcms_code = item['rcms_code']
                            break
                
                if row_id is None or row_id not in existing_ids:
                    new_row = {
                        '통계목명': str(row['통계목명']),
                        '사용일자': date_str,
                        '지출결의명': str(row['지출결의명']),
                        '상세내역': str(row['상세내역']) if pd.notna(row['상세내역']) else "",
                        '지출결의액': int(float(str(row['지출결의액']).replace(',', ''))) if pd.notna(row['지출결의액']) else 0,
                        'rcms_code': rcms_code,
                        'rcms_name': rcms_name,
                        'rcms_settled': bool(row['rcms_settled']) if pd.notna(row['rcms_settled']) else False
                    }
                    new_rows.append(new_row)
                else:
                    updated_row = {
                        'id': row_id,
                        '통계목명': str(row['통계목명']),
                        '사용일자': date_str,
                        '지출결의명': str(row['지출결의명']),
                        '상세내역': str(row['상세내역']) if pd.notna(row['상세내역']) else "",
                        '지출결의액': int(float(str(row['지출결의액']).replace(',', ''))) if pd.notna(row['지출결의액']) else 0,
                        'rcms_code': rcms_code,
                        'rcms_name': rcms_name,
                        'rcms_settled': bool(row['rcms_settled']) if pd.notna(row['rcms_settled']) else False
                    }
                    updated_rows.append(updated_row)
            
            for new_row in new_rows:
                expense_manager.add_row(new_row)
            
            for updated_row in updated_rows:
                expense_manager.update_row(updated_row['id'], updated_row)
            
            # 삭제된 행 처리 (테이블에서 삭제된 행 자동 감지)
            if not current_df.empty:
                # edited_df에서 유효한 ID 추출
                edited_ids = set()
                for idx, row in edited_df.iterrows():
                    if pd.notna(row.get('id')):
                        try:
                            edited_ids.add(int(float(row['id'])))
                        except (ValueError, TypeError):
                            pass
                
                # 삭제된 ID 찾기 (기존 ID 중에서 edited_df에 없는 것)
                deleted_ids = existing_ids - edited_ids
                for deleted_id in deleted_ids:
                    expense_manager.delete_row(int(deleted_id))
            
            # 변경사항 확인을 위해 원본 데이터 백업
            original_expense_df = current_df.copy()
            original_erp_budget = st.session_state.erp_budget_df.copy()
            original_rcms_budget = st.session_state.rcms_budget_df.copy()
            
            # ERP/RCMS 집계 자동 실행
            expense_df = expense_manager.get_all()
            st.session_state.erp_budget_df = BudgetCalculator.calculate_erp_budget(
                expense_df, st.session_state.erp_budget_df
            )
            st.session_state.rcms_budget_df, _ = BudgetCalculator.calculate_rcms_budget(
                expense_df, st.session_state.rcms_budget_df
            )
            
            # 변경사항 확인
            has_changes = has_data_changes(
                new_rows, updated_rows, deleted_ids,
                original_expense_df, expense_df,
                original_erp_budget, st.session_state.erp_budget_df,
                original_rcms_budget, st.session_state.rcms_budget_df
            )
            
            if not has_changes:
                if 'edited_expense_df' in st.session_state:
                    del st.session_state.edited_expense_df
                st.info("ℹ️ 변경사항이 없습니다.")
                return
            
            # 모든 데이터 저장
            data = {
                'EXPENSE': expense_manager.get_all(),
                'ERP_BUDGET': st.session_state.erp_budget_df,
                'RCMS_BUDGET': st.session_state.rcms_budget_df,
                'MAPPING_ERP_RCMS': st.session_state.mapping_df
            }
            
            success, error_msg = st.session_state.data_manager.save_all(data)
            if success:
                if 'edited_expense_df' in st.session_state:
                    del st.session_state.edited_expense_df
                st.success("✅ 지출내역이 저장되었고, ERP/RCMS 예산이 자동으로 집계되었습니다!")
                st.rerun()
            else:
                st.error(f"저장에 실패했습니다: {error_msg}")


def show_erp_budget_page():
    """ERP 예산 현황 페이지"""
    st.header("📈 ERP 예산 현황")
    
    if st.session_state.erp_budget_df.empty:
        st.warning("ERP 예산 데이터가 없습니다.")
        return
    
    # 작업 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ 예산 수정", key="edit_erp_btn"):
            st.session_state.edit_erp_budget = True
    
    # 예산 수정 모드
    if st.session_state.get('edit_erp_budget', False):
        st.subheader("예산 수정")
        st.caption("💡 **안내**: '총액'은 다른 항목들의 합계로 자동 계산됩니다.")
        edited_df = st.data_editor(
            st.session_state.erp_budget_df[['통계목명', '실행예산']],
            use_container_width=True,
            key="erp_editor",
            column_config={
                "통계목명": st.column_config.TextColumn("통계목명", disabled=True),
                "실행예산": st.column_config.NumberColumn(
                    "실행예산", 
                    step=1000, 
                    format="%d",
                    help="음수 가능"
                )
            }
        )
        col_save_erp1, col_save_erp2 = st.columns(2)
        with col_save_erp1:
            if st.button("💾 저장", key="save_erp_edit_btn", type="primary"):
                # 변경사항 확인을 위해 원본 백업
                original_erp_budget = st.session_state.erp_budget_df.copy()
                
                # "총액"을 제외한 항목들의 실행예산 업데이트
                other_items_mask = edited_df['통계목명'] != '총액'
                st.session_state.erp_budget_df.loc[other_items_mask, '실행예산'] = edited_df.loc[other_items_mask, '실행예산'].values
                
                # "총액"의 실행예산은 다른 항목들의 합계로 자동 계산
                total_budget = int(edited_df[edited_df['통계목명'] != '총액']['실행예산'].sum())
                total_row_idx = st.session_state.erp_budget_df[st.session_state.erp_budget_df['통계목명'] == '총액'].index
                if len(total_row_idx) > 0:
                    st.session_state.erp_budget_df.loc[total_row_idx[0], '실행예산'] = total_budget
                
                # 변경사항 확인 (실행예산만 비교)
                original_budget = original_erp_budget[['통계목명', '실행예산']].sort_values('통계목명').reset_index(drop=True)
                current_budget = st.session_state.erp_budget_df[['통계목명', '실행예산']].sort_values('통계목명').reset_index(drop=True)
                has_changes = not original_budget.equals(current_budget)
                
                if not has_changes:
                    st.info("ℹ️ 변경사항이 없습니다.")
                    st.session_state.edit_erp_budget = False
                    st.rerun()
                    return
                
                st.session_state.edit_erp_budget = False
                # ERP 집계 다시 실행
                if st.session_state.expense_manager:
                    expense_df = st.session_state.expense_manager.get_all()
                    st.session_state.erp_budget_df = BudgetCalculator.calculate_erp_budget(
                        expense_df, st.session_state.erp_budget_df
                    )
                # 저장
                data = {
                    'EXPENSE': st.session_state.expense_manager.get_all(),
                    'ERP_BUDGET': st.session_state.erp_budget_df,
                    'RCMS_BUDGET': st.session_state.rcms_budget_df,
                    'MAPPING_ERP_RCMS': st.session_state.mapping_df
                }
                success, error_msg = st.session_state.data_manager.save_all(data)
                if success:
                    st.success("✅ 예산이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error(f"저장 실패: {error_msg}")
        with col_save_erp2:
            if st.button("취소", key="cancel_erp_edit_btn"):
                st.session_state.edit_erp_budget = False
                st.rerun()
    else:
        # 집계 자동 실행 (지출내역 저장 시 자동으로 집계됨)
        if st.session_state.expense_manager:
            expense_df = st.session_state.expense_manager.get_all()
            st.session_state.erp_budget_df = BudgetCalculator.calculate_erp_budget(
                expense_df, st.session_state.erp_budget_df
            )
        
        # 테이블 표시
        display_erp_budget_table(st.session_state.erp_budget_df)
        
        # 차트
        st.markdown("---")
        plot_erp_budget_chart(st.session_state.erp_budget_df)
        
        # 요약 정보
        st.markdown("---")
        summary = BudgetCalculator.get_erp_summary(st.session_state.erp_budget_df)
        show_summary_cards(summary)
        


def show_execution_result_page():
    """집행 결과 통합 페이지 (ERP-RCMS 비교)"""
    st.header("📊 집행 결과")
    
    # 데이터 검증
    if st.session_state.erp_budget_df.empty or st.session_state.rcms_budget_df.empty:
        st.warning("예산 데이터가 없습니다. 지출내역을 먼저 입력해주세요.")
        return
    
    # 집계 자동 실행 (지출내역 저장 시 또는 예산 수정 후 자동으로 집계됨)
    # 예산 수정 모드가 아닐 때만 집계 실행 (수정 모드에서는 저장 시 집계됨)
    if not st.session_state.get('edit_erp_budget', False) and not st.session_state.get('edit_rcms_budget', False):
        if st.session_state.expense_manager:
            expense_df = st.session_state.expense_manager.get_all()
            st.session_state.erp_budget_df = BudgetCalculator.calculate_erp_budget(
                expense_df, st.session_state.erp_budget_df
            )
            st.session_state.rcms_budget_df, unsettled_info = BudgetCalculator.calculate_rcms_budget(
                expense_df, st.session_state.rcms_budget_df
            )
        else:
            unsettled_info = {"미정산_금액": 0, "미정산_건수": 0, "미정산_ID_목록": []}
    else:
        # 예산 수정 모드일 때는 미정산 정보만 계산
        if st.session_state.expense_manager:
            expense_df = st.session_state.expense_manager.get_all()
            _, unsettled_info = BudgetCalculator.calculate_rcms_budget(
                expense_df, st.session_state.rcms_budget_df
            )
        else:
            unsettled_info = {"미정산_금액": 0, "미정산_건수": 0, "미정산_ID_목록": []}
    
    # 총액 계산 및 검증 (정산 완료된 항목만 집계)
    # ERP 총액은 "총액" 행의 값 사용 (다른 항목들의 합계)
    erp_total_row = st.session_state.erp_budget_df[st.session_state.erp_budget_df['통계목명'] == '총액']
    if not erp_total_row.empty:
        erp_total_executed = int(erp_total_row['집행액'].iloc[0])
        erp_total_budget = int(erp_total_row['실행예산'].iloc[0])
    else:
        # "총액" 행이 없으면 다른 항목들의 합계
        other_items = st.session_state.erp_budget_df[st.session_state.erp_budget_df['통계목명'] != '총액']
        erp_total_executed = int(other_items['집행액'].sum())
        erp_total_budget = int(other_items['실행예산'].sum())
    
    rcms_total_executed = int(st.session_state.rcms_budget_df['used_amount'].sum())
    rcms_total_budget = int(st.session_state.rcms_budget_df['budget_amount'].sum())
    
    # 미정산 항목 정보는 이미 calculate_rcms_budget에서 계산됨
    unsettled_ids = unsettled_info.get('미정산_ID_목록', [])
    unsettled_amount = unsettled_info.get('미정산_금액', 0)
    unsettled_count = unsettled_info.get('미정산_건수', 0)
    
    # 검증: 집행액은 무조건 같아야 함 (ERP는 전체, RCMS는 정산 완료된 항목만 집계)
    is_executed_valid = (erp_total_executed == rcms_total_executed)
    
    # 상단 요약 및 검증
    st.subheader("📈 집행 결과 요약 (ERP: 전체, RCMS: 정산 완료 항목만)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ERP 총 집행액", format_currency(erp_total_executed))
    with col2:
        st.metric("RCMS 총 집행액", format_currency(rcms_total_executed))
    with col3:
        if is_executed_valid:
            st.success("✅ 집행액 일치")
        else:
            diff = abs(erp_total_executed - rcms_total_executed)
            st.error(f"❌ 집행액 불일치\n(차이: {format_currency(diff)})")
    with col4:
        budget_diff = abs(erp_total_budget - rcms_total_budget)
        if budget_diff == 0:
            st.info("예산 동일")
        else:
            st.info(f"예산 차이\n{format_currency(budget_diff)}")
    
    # 미정산 항목 정보 표시
    if unsettled_count > 0:
        st.markdown("---")
        st.warning(f"⚠️ **미정산 항목**: {unsettled_count}건, 총 {format_currency(unsettled_amount)}")
        if unsettled_ids:
            st.write(f"**미정산 항목 ID**: {', '.join(map(str, sorted(unsettled_ids)))}")
            st.caption("💡 **안내**: 위 ID의 항목들은 RCMS 정산 여부 체크가 안 되어 있어 RCMS 집행액에 포함되지 않습니다.")
    
    st.caption("💡 **참고**: ERP는 모든 항목을 집계하고, RCMS는 정산 완료된 항목만 집계합니다. 집행액은 동일 금액이므로 일치해야 합니다. 실행예산은 ERP와 RCMS 분류 기준이 다르므로 차이가 있을 수 있습니다.")
    
    st.markdown("---")
    
    # 예산 수정 버튼
    col_edit1, col_edit2 = st.columns(2)
    with col_edit1:
        if st.button("✏️ ERP 예산 수정", key="edit_erp_btn"):
            st.session_state.edit_erp_budget = True
    with col_edit2:
        if st.button("✏️ RCMS 예산 수정", key="edit_rcms_btn"):
            st.session_state.edit_rcms_budget = True
    
    # ERP 예산 수정 모드
    if st.session_state.get('edit_erp_budget', False):
        st.markdown("---")
        st.subheader("ERP 예산 수정")
        st.caption("💡 **안내**: '총액'은 다른 항목들의 합계로 자동 계산됩니다.")
        edited_df = st.data_editor(
            st.session_state.erp_budget_df[['통계목명', '실행예산']],
            use_container_width=True,
            key="erp_editor_unified",
            column_config={
                "통계목명": st.column_config.TextColumn("통계목명", disabled=True),
                "실행예산": st.column_config.NumberColumn(
                    "실행예산", 
                    step=1000, 
                    format="%d",
                    help="음수 가능"
                )
            }
        )
        col_save_erp1, col_save_erp2 = st.columns(2)
        with col_save_erp1:
            if st.button("💾 저장", key="save_erp_edit_btn_unified", type="primary"):
                # 변경사항 확인을 위해 원본 백업
                original_erp_budget = st.session_state.erp_budget_df.copy()
                
                # "총액"을 제외한 항목들의 실행예산 업데이트
                other_items_mask = edited_df['통계목명'] != '총액'
                st.session_state.erp_budget_df.loc[other_items_mask, '실행예산'] = edited_df.loc[other_items_mask, '실행예산'].values
                
                # "총액"의 실행예산은 다른 항목들의 합계로 자동 계산
                total_budget = int(edited_df[edited_df['통계목명'] != '총액']['실행예산'].sum())
                total_row_idx = st.session_state.erp_budget_df[st.session_state.erp_budget_df['통계목명'] == '총액'].index
                if len(total_row_idx) > 0:
                    st.session_state.erp_budget_df.loc[total_row_idx[0], '실행예산'] = total_budget
                
                # 변경사항 확인 (실행예산만 비교)
                original_budget = original_erp_budget[['통계목명', '실행예산']].sort_values('통계목명').reset_index(drop=True)
                current_budget = st.session_state.erp_budget_df[['통계목명', '실행예산']].sort_values('통계목명').reset_index(drop=True)
                has_changes = not original_budget.equals(current_budget)
                
                if not has_changes:
                    st.info("ℹ️ 변경사항이 없습니다.")
                    st.session_state.edit_erp_budget = False
                    st.rerun()
                    return
                
                st.session_state.edit_erp_budget = False
                # ERP 집계 다시 실행
                if st.session_state.expense_manager:
                    expense_df = st.session_state.expense_manager.get_all()
                    st.session_state.erp_budget_df = BudgetCalculator.calculate_erp_budget(
                        expense_df, st.session_state.erp_budget_df
                    )
                # 저장
                data = {
                    'EXPENSE': st.session_state.expense_manager.get_all(),
                    'ERP_BUDGET': st.session_state.erp_budget_df,
                    'RCMS_BUDGET': st.session_state.rcms_budget_df,
                    'MAPPING_ERP_RCMS': st.session_state.mapping_df
                }
                success, error_msg = st.session_state.data_manager.save_all(data)
                if success:
                    st.success("✅ 예산이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error(f"저장 실패: {error_msg}")
        with col_save_erp2:
            if st.button("취소", key="cancel_erp_edit_btn_unified"):
                st.session_state.edit_erp_budget = False
                st.rerun()
        return
    
    # RCMS 예산 수정 모드
    if st.session_state.get('edit_rcms_budget', False):
        st.markdown("---")
        st.subheader("RCMS 예산 수정")
        edited_df = st.data_editor(
            st.session_state.rcms_budget_df[['rcms_code', 'rcms_name', 'budget_amount']],
            use_container_width=True,
            key="rcms_editor",
            column_config={
                "rcms_code": st.column_config.TextColumn("RCMS 코드", disabled=True),
                "rcms_name": st.column_config.TextColumn("RCMS 항목명", disabled=True),
                "budget_amount": st.column_config.NumberColumn(
                    "예산 금액", 
                    step=1000, 
                    format="%d",
                    help="음수 가능"
                )
            }
        )
        col_save_rcms1, col_save_rcms2 = st.columns(2)
        with col_save_rcms1:
            if st.button("💾 저장", key="save_rcms_edit_btn", type="primary"):
                # 변경사항 확인을 위해 원본 백업
                original_rcms_budget = st.session_state.rcms_budget_df.copy()
                
                # rcms_code를 기준으로 budget_amount 업데이트
                for idx, row in edited_df.iterrows():
                    # rcms_code를 문자열로 변환하여 비교 (데이터 타입 일치)
                    rcms_code = str(row['rcms_code']).strip() if pd.notna(row['rcms_code']) else ""
                    budget_amount = int(float(row['budget_amount'])) if pd.notna(row['budget_amount']) else 0
                    # rcms_code로 매칭하여 업데이트 (문자열로 변환하여 비교)
                    mask = st.session_state.rcms_budget_df['rcms_code'].astype(str).str.strip() == rcms_code
                    if mask.any():
                        st.session_state.rcms_budget_df.loc[mask, 'budget_amount'] = budget_amount
                
                # 변경사항 확인 (budget_amount만 비교)
                original_rcms = original_rcms_budget[['rcms_code', 'rcms_name', 'budget_amount']].sort_values('rcms_code').reset_index(drop=True)
                current_rcms = st.session_state.rcms_budget_df[['rcms_code', 'rcms_name', 'budget_amount']].sort_values('rcms_code').reset_index(drop=True)
                has_changes = not original_rcms.equals(current_rcms)
                
                if not has_changes:
                    st.info("ℹ️ 변경사항이 없습니다.")
                    st.session_state.edit_rcms_budget = False
                    st.rerun()
                    return
                
                st.session_state.edit_rcms_budget = False
                # RCMS 집계 다시 실행
                if st.session_state.expense_manager:
                    expense_df = st.session_state.expense_manager.get_all()
                    st.session_state.rcms_budget_df, _ = BudgetCalculator.calculate_rcms_budget(
                        expense_df, st.session_state.rcms_budget_df
                    )
                # 저장
                data = {
                    'EXPENSE': st.session_state.expense_manager.get_all(),
                    'ERP_BUDGET': st.session_state.erp_budget_df,
                    'RCMS_BUDGET': st.session_state.rcms_budget_df,
                    'MAPPING_ERP_RCMS': st.session_state.mapping_df
                }
                success, error_msg = st.session_state.data_manager.save_all(data)
                if success:
                    st.success("✅ 예산이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error(f"저장 실패: {error_msg}")
        with col_save_rcms2:
            if st.button("취소", key="cancel_rcms_edit_btn"):
                st.session_state.edit_rcms_budget = False
                st.rerun()
        return
    
    # 좌우 비교 레이아웃
    st.markdown("---")
    st.subheader("📊 ERP vs RCMS 집행 현황 비교")
    
    col_left, col_right = st.columns(2)
    
    # 왼쪽: ERP 예산 현황
    with col_left:
        st.markdown("### 📈 ERP 예산 현황")
        
        # ERP 요약
        erp_summary = BudgetCalculator.get_erp_summary(st.session_state.erp_budget_df)
        col_erp1, col_erp2 = st.columns(2)
        with col_erp1:
            st.metric("총 예산", format_currency(erp_summary['총_예산']))
            st.metric("총 집행액", format_currency(erp_summary['총_집행액']))
        with col_erp2:
            st.metric("총 잔액", format_currency(erp_summary['총_잔액']))
            st.metric("총 집행률", f"{erp_summary['총_집행률']:.2f}%")
        
        # ERP 테이블
        display_erp_budget_table(st.session_state.erp_budget_df)
    
    # 오른쪽: RCMS 예산 현황
    with col_right:
        st.markdown("### 📊 RCMS 예산 현황")
        
        # RCMS 요약
        rcms_total_budget = int(st.session_state.rcms_budget_df['budget_amount'].sum())
        rcms_total_used = int(st.session_state.rcms_budget_df['used_amount'].sum())
        rcms_total_balance = int(st.session_state.rcms_budget_df['balance'].sum())
        rcms_total_rate = (rcms_total_used / rcms_total_budget * 100) if rcms_total_budget > 0 else 0.0
        
        col_rcms1, col_rcms2 = st.columns(2)
        with col_rcms1:
            st.metric("총 예산", format_currency(rcms_total_budget))
            st.metric("총 집행액", format_currency(rcms_total_used))
        with col_rcms2:
            st.metric("총 잔액", format_currency(rcms_total_balance))
            st.metric("총 집행률", f"{rcms_total_rate:.2f}%")
        
        # RCMS 테이블
        display_rcms_budget_table(st.session_state.rcms_budget_df)
        
        # 미정산 정보
        if st.session_state.expense_manager:
            expense_df = st.session_state.expense_manager.get_all()
            _, unsettled_info = BudgetCalculator.calculate_rcms_budget(
                expense_df, st.session_state.rcms_budget_df
            )
            st.markdown("---")
            st.markdown("#### 미정산 정보")
            col_un1, col_un2 = st.columns(2)
            with col_un1:
                st.metric("총 미정산 금액", format_currency(unsettled_info['미정산_금액']))
            with col_un2:
                st.metric("미정산 건수", unsettled_info['미정산_건수'])
    
    # 시각화 섹션
    st.markdown("---")
    st.subheader("📈 집행 결과 시각화")
    
    # ERP 집행률 차트
    st.markdown("#### ERP 통계목별 집행률")
    plot_erp_budget_chart(st.session_state.erp_budget_df)
    
    # RCMS 집행률 차트
    st.markdown("#### RCMS 항목별 집행률")
    plot_rcms_budget_chart(st.session_state.rcms_budget_df)
        




# 메인 실행
if __name__ == "__main__":
    if st.session_state.page == 'file_select':
        show_file_select_page()
    else:
        if not st.session_state.current_file_path:
            st.session_state.page = 'file_select'
            st.rerun()
        show_main_page()

