"""
재사용 가능한 UI 컴포넌트 모듈
Streamlit 컴포넌트
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import format_currency, format_number


def display_file_info(file_path: str, folder_path: str):
    """파일 정보 표시"""
    st.info(f"**현재 파일**: `{file_path}`")
    st.caption(f"**폴더**: `{folder_path}`")


def display_expense_table(df: pd.DataFrame, editable: bool = False):
    """지출내역 테이블 표시"""
    if df.empty:
        st.info("지출내역이 없습니다.")
        return df
    
    # 표시용 컬럼 선택 (일부 컬럼은 숨김)
    display_columns = ['id', '통계목명', '사용일자', '지출결의명', '상세내역', 
                      '지출결의액', 'rcms_code', 'rcms_name', 'rcms_settled']
    
    display_df = df[display_columns].copy()
    
    # 금액 포맷팅
    if '지출결의액' in display_df.columns:
        display_df['지출결의액'] = display_df['지출결의액'].apply(lambda x: format_currency(int(x)) if pd.notna(x) else "")
    
    # rcms_settled를 체크박스로 표시
    if 'rcms_settled' in display_df.columns:
        display_df['rcms_settled'] = display_df['rcms_settled'].apply(lambda x: "✓" if x else "")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    return df


def display_erp_budget_table(df: pd.DataFrame, editable: bool = False):
    """ERP 예산 테이블 표시 (스크롤 없이 한눈에 보이도록)"""
    if df.empty:
        st.info("ERP 예산 데이터가 없습니다.")
        return df
    
    display_df = df.copy()
    
    # updated_at 컬럼 제외 (표에 표시하지 않음)
    if 'updated_at' in display_df.columns:
        # 업데이트 시간 추출 (첫 번째 행의 시간 사용, 모든 행이 같은 시간이어야 함)
        update_time = None
        if not display_df['updated_at'].empty:
            first_time = display_df['updated_at'].iloc[0]
            if pd.notna(first_time):
                from datetime import datetime
                if isinstance(first_time, datetime):
                    update_time = first_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    update_time = str(first_time)
        
        # updated_at 컬럼 제거
        display_df = display_df.drop(columns=['updated_at'])
        
        # 업데이트 시간 표시 (테이블 위에 하나만)
        if update_time:
            st.caption(f"📅 마지막 업데이트: {update_time}")
    
    # 금액 포맷팅
    for col in ['실행예산', '집행액', '잔액']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: format_currency(int(x)) if pd.notna(x) else "")
    
    # 집행률 포맷팅
    if '집행률' in display_df.columns:
        display_df['집행률'] = display_df['집행률'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
    
    # 스크롤 없이 한눈에 보이도록 CSS 스타일 적용
    st.markdown("""
    <style>
    .stDataFrame {
        max-height: 600px;
        overflow: visible !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    return df


def display_rcms_budget_table(df: pd.DataFrame, editable: bool = False):
    """RCMS 예산 테이블 표시 (통합 표, 항목명 포함, 같은 항목은 첫 행에만 표시)"""
    if df.empty:
        st.info("RCMS 예산 데이터가 없습니다.")
        return df
    
    display_df = df.copy()
    
    # parent_category가 있으면 첫 번째 컬럼으로 배치
    if 'parent_category' in display_df.columns:
        # parent_category로 정렬 (같은 항목이 연속으로 나오도록)
        display_df = display_df.sort_values('parent_category').reset_index(drop=True)
        
        # 같은 항목이 연속으로 나올 때 첫 번째 행에만 항목명 표시 (나머지는 빈 문자열)
        display_df['parent_category_display'] = display_df['parent_category']
        for i in range(1, len(display_df)):
            if display_df.loc[i, 'parent_category'] == display_df.loc[i-1, 'parent_category']:
                display_df.loc[i, 'parent_category_display'] = ""
        
        # 컬럼 순서: parent_category_display, rcms_name, budget_amount, used_amount, balance, rate (코드 제외)
        display_df = display_df[['parent_category_display', 'rcms_name', 'budget_amount', 'used_amount', 'balance', 'rate']].copy()
    else:
        # parent_category가 없으면 기존 방식 (코드 제외)
        display_df = display_df[['rcms_name', 'budget_amount', 'used_amount', 'balance', 'rate']].copy()
    
    # 금액 포맷팅
    for col in ['budget_amount', 'used_amount', 'balance']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: format_currency(int(x)) if pd.notna(x) else "")
    
    # rate 포맷팅
    if 'rate' in display_df.columns:
        display_df['rate'] = display_df['rate'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%")
    
    # 컬럼명 변경
    if 'parent_category_display' in display_df.columns:
        display_df.columns = ['항목', '세부항목', '예산', '사용액', '잔액', '집행률']
    else:
        display_df.columns = ['세부항목', '예산', '사용액', '잔액', '집행률']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    return df


def plot_erp_budget_chart(df: pd.DataFrame):
    """ERP 예산 집행률 바 차트"""
    if df.empty or '집행률' not in df.columns:
        return
    
    # 집행률이 있는 항목만 필터링
    chart_df = df[df['실행예산'] > 0].copy()
    if chart_df.empty:
        st.info("집행률을 표시할 데이터가 없습니다.")
        return
    
    # 색상 설정 (집행률에 따라)
    chart_df['color'] = chart_df['집행률'].apply(
        lambda x: 'red' if x > 100 else ('orange' if x >= 80 else 'green')
    )
    
    fig = px.bar(
        chart_df,
        x='통계목명',
        y='집행률',
        color='color',
        color_discrete_map={'red': '#FF4444', 'orange': '#FFA500', 'green': '#44AA44'},
        title='ERP 통계목별 집행률',
        labels={'집행률': '집행률 (%)', '통계목명': '통계목'}
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def plot_rcms_budget_chart(df: pd.DataFrame):
    """RCMS 예산 집행률 바 차트"""
    if df.empty or 'rate' not in df.columns:
        return
    
    # rate가 있는 항목만 필터링
    chart_df = df[df['budget_amount'] > 0].copy()
    if chart_df.empty:
        st.info("집행률을 표시할 데이터가 없습니다.")
        return
    
    # 색상 설정
    chart_df['color'] = chart_df['rate'].apply(
        lambda x: 'red' if x > 100 else ('orange' if x >= 80 else 'green')
    )
    
    fig = px.bar(
        chart_df,
        x='rcms_name',
        y='rate',
        color='color',
        color_discrete_map={'red': '#FF4444', 'orange': '#FFA500', 'green': '#44AA44'},
        title='RCMS 항목별 집행률',
        labels={'rate': '집행률 (%)', 'rcms_name': 'RCMS 항목'}
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def show_summary_cards(summary: dict):
    """요약 정보 카드 표시"""
    cols = st.columns(len(summary))
    for idx, (key, value) in enumerate(summary.items()):
        with cols[idx]:
            st.metric(
                label=key.replace('_', ' '),
                value=format_currency(value) if isinstance(value, int) and '금액' in key or '예산' in key or '집행액' in key or '잔액' in key
                else (f"{value}%" if '률' in key else format_number(value) if isinstance(value, int) else value)
            )

