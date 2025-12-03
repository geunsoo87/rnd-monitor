# Streamlit Cloud 배포 가이드

## 1. GitHub 저장소 준비

1. GitHub에 새 저장소 생성
2. 현재 프로젝트 파일들을 GitHub에 푸시:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/사용자명/저장소명.git
   git push -u origin main
   ```

## 2. Streamlit Cloud에 배포

1. https://streamlit.io/cloud 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. 다음 정보 입력:
   - **Repository**: 방금 만든 GitHub 저장소 선택
   - **Branch**: `main` (또는 `master`)
   - **Main file path**: `app.py`
5. "Deploy" 클릭

## 3. 사용 방법

### 파일 업로드
- "기존 파일 열기"에서 `master.xlsx` 파일을 업로드하여 작업 시작

### 새 파일 생성
- "새 파일로 시작" 버튼을 클릭하여 새로운 파일로 시작

### 저장 및 다운로드
- 작업 후 "💾 반영저장" 버튼 클릭
- 저장 완료 후 "📥 파일 다운로드" 버튼이 나타남
- 다운로드 버튼을 클릭하여 로컬에 저장

## 4. 주의사항

- Streamlit Cloud는 무료 플랜에서도 사용 가능하지만, 세션이 비활성화되면 데이터가 삭제될 수 있습니다
- 중요한 데이터는 반드시 다운로드하여 로컬에 백업하세요
- 파일은 임시 저장소(`temp` 폴더)에 저장되므로, 세션이 종료되면 사라질 수 있습니다

## 5. 로컬 실행 (대안)

로컬에서 실행하려면:
```bash
streamlit run app.py
```

또는 `실행.bat` 파일을 더블클릭

