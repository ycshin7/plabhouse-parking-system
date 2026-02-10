# Slack Webhook 및 GitHub 데이터 저장 설정 가이드

## 📱 Slack Webhook URL 받는 방법

### 1단계: Slack API 페이지 접속
1. 웹 브라우저에서 **https://api.slack.com/apps** 접속
2. 회사 Slack 계정으로 로그인

### 2단계: 새 앱 만들기
1. **"앱 만들기"** (Create New App) 버튼 클릭
2. **"처음부터"** (From scratch) 선택
3. 앱 이름 입력: `플랩하우스 주차 알림`
4. 워크스페이스 선택: 회사 Slack 워크스페이스
5. **"앱 만들기"** 클릭

### 3단계: Incoming Webhooks 활성화
1. 왼쪽 메뉴에서 **"수신 웹후크"** (Incoming Webhooks) 클릭
2. 오른쪽 상단 스위치를 **"켜기"** (On)로 변경
3.    - ⚠️ **중요**: 이 단계를 꼭 해야 합니다!

### 4단계: Webhook URL 생성
1. 페이지 아래로 스크롤
2. **"워크스페이스에 새 웹후크 추가"** (Add New Webhook to Workspace) 버튼 클릭
3. 메시지를 보낼 채널 선택 (예: #주차, #공지)
4. **"허용"** (Allow) 버튼 클릭

### 5단계: Webhook URL 복사
화면에 **Webhook URL**이 나타납니다:

```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

**"복사"** (Copy) 버튼을 클릭하여 URL을 복사하세요!

---

## 🔐 Streamlit Cloud에 Secrets 설정하기 (중요)

데이터가 사라지지 않게 하려면 **Slack URL** 뿐만 아니라 **GitHub 계정 정보**도 꼭 넣어야 합니다.

### 방법 1: Streamlit Cloud 웹사이트에서 설정 (추천)

1. **https://share.streamlit.io/** 접속
2. 로그인 후 **"Your apps"** 클릭
3. **"plabhouse-parking-system"** 앱 찾기
4. 앱 이름 옆 **⋮ (점 3개)** 클릭
5. **"Settings"** 선택
6. 왼쪽 메뉴에서 **"Secrets"** 클릭
7. 아래 내용을 입력 (기존 내용 아래에 추가):

```toml
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

# GitHub 데이터 저장용 (데이터 유실 방지!)
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxx"
GITHUB_REPO = "사용자이름/저장소이름"
```

- **GITHUB_TOKEN**: GitHub Personal Access Token (Repo 권한 필요)
- **GITHUB_REPO**: `yoonc/plabhouse-parking` 처럼 `아이디/저장소명` 형식

**주의**: 예전에 `REPO_NAME`을 썼다면 지우고 `GITHUB_REPO`로 통일해주세요!

8. **"Save"** 클릭
9. 앱이 자동으로 재시작됩니다 (1-2분 소요)

---

## ✅ 테스트 방법

### Slack 알림 테스트
1. 관리자 페이지 → 배정 결과 탭
2. **"📢 슬랙으로 결과 전송"** 버튼 클릭
3. Slack 채널 확인

### 데이터 저장 테스트
1. 주차 신청 또는 관리자 예외 등록을 해보세요.
2. 화면 오른쪽 위에 **"✅ ... 저장 완료 (GitHub)"** 라는 메시지가 뜨면 성공!
3. **"⚠️ ... GitHub 저장 실패"** 라고 뜨면 Secrets 설정을 다시 확인해주세요.

---

## 🔧 requirements.txt 확인

`requests` 및 `PyGithub` 라이브러리가 필요합니다.

```
requests
PyGithub
```

없으면 추가하고 GitHub에 push하세요!
