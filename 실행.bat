@echo off
chcp 65001 >nul
title 연구비 예산관리 시스템
color 0B
echo.
echo ========================================
echo   연구비 예산관리 시스템
echo ========================================
echo.

REM 현재 스크립트 위치
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PORTABLE=%SCRIPT_DIR%python\python.exe"

REM Python Portable 확인
if exist "%PYTHON_PORTABLE%" (
    echo [포터블 버전] Python Portable을 사용합니다.
    set "PYTHON_CMD=%PYTHON_PORTABLE%"
    goto check_packages
)

REM 시스템 Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo 해결 방법:
    echo 1. Python 3.10 이상을 설치하세요
    echo    다운로드: https://www.python.org/downloads/
    echo 2. 또는 포터블 버전을 사용하세요
    echo    "python" 폴더에 Python Portable을 설치하세요
    echo.
    pause
    exit /b 1
)

echo [일반 버전] 시스템 Python을 사용합니다.
set "PYTHON_CMD=python"

:check_packages
echo.
echo [1/2] 패키지 확인 중...

REM 패키지 확인
%PYTHON_CMD% -m pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo 패키지가 설치되어 있지 않습니다.
    echo 자동으로 설치를 시작합니다...
    echo.
    echo 이 작업은 몇 분 정도 걸릴 수 있습니다.
    echo 잠시만 기다려주세요...
    echo.
    
    %PYTHON_CMD% -m pip install --upgrade pip --quiet
    %PYTHON_CMD% -m pip install -r "%SCRIPT_DIR%requirements.txt"
    
    if errorlevel 1 (
        echo.
        echo [오류] 패키지 설치에 실패했습니다.
        echo 인터넷 연결을 확인하거나 관리자 권한으로 실행해보세요.
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo 설치 완료!
)

echo [2/2] 프로그램 시작 중...
echo.
echo ========================================
echo   프로그램을 시작합니다...
echo ========================================
echo.
echo 브라우저가 자동으로 열립니다.
echo 잠시만 기다려주세요...
echo.
echo 이 창을 닫으면 프로그램이 종료됩니다.
echo.

REM Streamlit 앱 실행
cd /d "%SCRIPT_DIR%"
%PYTHON_CMD% -m streamlit run app.py --server.headless true

pause

