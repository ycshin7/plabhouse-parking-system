# 🚗 Parking System (주차 배정 시스템)

이 프로젝트는 Streamlit으로 제작된 주차 배정 및 관리 시스템입니다.

## 🛠️ 배포 가이드 (Streamlit Community Cloud)

이 앱은 **Streamlit Community Cloud**를 통해 무료로 가장 쉽게 배포할 수 있습니다.
(Vercel은 Streamlit의 실시간 통신(Websocket)을 완벽하게 지원하지 않아 권장하지 않습니다.)

### 1단계: GitHub에 코드 올리기
1. GitHub에 로그인하고 **New Repository**를 만듭니다.
2. 이 폴더의 모든 파일(`app.py`, `requirements.txt`, `users.json` 등)을 업로드합니다.

### 2단계: Streamlit Cloud 배포
1. [share.streamlit.io](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
2. **"New app"** 버튼을 클릭합니다.
3. 방금 만든 **GitHub Repository**를 선택합니다.
4. **Main file path**에 `app.py`가 입력되어 있는지 확인합니다.
5. **"Deploy!"** 버튼을 누르면 끝! 🚀

---

## ⚠️ 중요: 데이터 저장 관련 주의사항

현재 이 앱은 데이터를 `json` 파일(`users.json`, `history.json` 등)에 저장하고 있습니다.
**클라우드 배포 환경(Streamlit Cloud, Vercel 등)에서는 앱이 재시작될 때마다 이 파일들이 초기화됩니다.**

즉, 배포 후 직원을 등록하거나 주차 신청을 해도, **앱이 절전 모드에 들어가거나 업데이트되면 데이터가 사라질 수 있습니다.**

데이터를 영구적으로 저장하려면 **Google Sheets**나 **데이터베이스**를 연동해야 합니다.
(현재 버전은 로컬 실행 또는 데모 목적으로 적합합니다.)

## 📦 설치 패키지
- streamlit
- pandas
- openpyxl
