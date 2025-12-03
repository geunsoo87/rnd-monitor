# Streamlit Cloud 배포 가이드

이 문서는 연구비 예산관리 시스템을 Streamlit Cloud에 배포하는 방법을 안내합니다.

## 사전 준비

### 1. GitHub 계정 및 저장소 생성

1. **GitHub 계정 생성** (없는 경우)
   - https://github.com 에서 계정 생성

2. **새 저장소 생성**
   - GitHub에서 "New repository" 클릭
   - Repository name: `rnd-monitor` (또는 원하는 이름)
   - Description: "연구비 예산관리 시스템"
   - Public 또는 Private 선택
   - "Initialize this repository with a README" 체크 해제
   - "Create repository" 클릭

### 2. 로컬 Git 저장소 초기화 및 업로드

```bash
# 프로젝트 폴더로 이동
cd C:\Users\geuns\PythonCode\rnd_monitor

# Git 초기화
git init

# .gitignore 확인 (이미 생성되어 있음)
git add .gitignore

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: 연구비 예산관리 시스템"

# GitHub 저장소 연결 (YOUR_USERNAME과 YOUR_REPO_NAME을 실제 값으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 메인 브랜치로 이름 변경 (필요한 경우)
git branch -M main

# GitHub에 푸시
git push -u origin main
```

### 3. Streamlit Cloud 배포

1. **Streamlit Cloud 접속**
   - https://share.streamlit.io 에서 GitHub 계정으로 로그인

2. **새 앱 배포**
   - "New app" 버튼 클릭
   - **Repository**: 위에서 생성한 GitHub 저장소 선택
   - **Branch**: `main` (또는 `master`)
   - **Main file path**: `app.py`
   - **App URL**: 원하는 URL 입력 (예: `rnd-monitor`)
   - "Deploy!" 클릭

3. **배포 완료**
   - 배포가 완료되면 자동으로 앱이 실행됩니다
   - URL은 `https://YOUR_APP_NAME.streamlit.app` 형식입니다

## 주의사항

### Streamlit Cloud 제한사항

1. **로컬 파일 시스템 접근 제한**
   - Streamlit Cloud에서는 로컬 파일 시스템에 직접 접근할 수 없습니다
   - 폴더 선택 다이얼로그 (tkinter)는 작동하지 않습니다
   - **해결 방법**: 파일 업로드 기능을 사용하세요

2. **데이터 저장**
   - Streamlit Cloud는 세션 기반이므로, 페이지를 새로고침하면 데이터가 초기화될 수 있습니다
   - **권장**: 파일을 다운로드하여 로컬에 저장하거나, 외부 스토리지(Google Drive, Dropbox 등)를 사용하세요

3. **파일 크기 제한**
   - 업로드 파일 크기 제한이 있을 수 있습니다
   - 큰 파일은 분할하여 업로드하거나 압축하여 사용하세요

### 로컬 실행 vs Cloud 배포

| 기능 | 로컬 실행 | Streamlit Cloud |
|------|----------|-----------------|
| 폴더 선택 다이얼로그 | ✅ 작동 | ❌ 작동 안 함 |
| 파일 업로드 | ✅ 작동 | ✅ 작동 |
| 파일 저장 | ✅ 로컬 저장 | ⚠️ 세션 내에서만 |
| 데이터 지속성 | ✅ 영구 저장 | ⚠️ 세션 종료 시 초기화 |

## 업데이트 배포

코드를 수정한 후 GitHub에 푸시하면 Streamlit Cloud가 자동으로 재배포합니다:

```bash
# 변경사항 커밋
git add .
git commit -m "업데이트 내용 설명"

# GitHub에 푸시
git push origin main
```

Streamlit Cloud는 자동으로 변경사항을 감지하고 재배포합니다.

## 문제 해결

### 배포 실패 시

1. **requirements.txt 확인**
   - 모든 의존성이 올바르게 나열되어 있는지 확인
   - 버전 호환성 확인

2. **로그 확인**
   - Streamlit Cloud 대시보드에서 "Manage app" → "Logs" 확인
   - 에러 메시지 확인

3. **일반적인 문제**
   - `ModuleNotFoundError`: requirements.txt에 누락된 패키지 추가
   - `ImportError`: 파일 경로 또는 import 문 확인
   - `FileNotFoundError`: 파일 경로가 올바른지 확인

### 로컬에서 테스트

배포 전에 로컬에서 테스트하는 것을 권장합니다:

```bash
streamlit run app.py
```

## 추가 리소스

- [Streamlit Cloud 문서](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit 배포 가이드](https://docs.streamlit.io/deploy)
- [GitHub 가이드](https://docs.github.com)

