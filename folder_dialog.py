"""
폴더 선택 다이얼로그 유틸리티
Windows에서 폴더 선택 다이얼로그를 띄우는 함수
"""
import os

# tkinter가 사용 가능한지 확인
try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


def select_folder(initial_dir=None):
    """폴더 선택 다이얼로그 표시"""
    if not TKINTER_AVAILABLE:
        # Streamlit Cloud 등 tkinter를 사용할 수 없는 환경
        return None
    
    try:
        # tkinter 루트 윈도우를 숨김
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # 폴더 선택 다이얼로그
        folder_path = filedialog.askdirectory(
            title="폴더 선택",
            initialdir=initial_dir if initial_dir and os.path.exists(initial_dir) else os.getcwd()
        )
        
        root.destroy()
        return folder_path if folder_path else None
    except Exception:
        return None

