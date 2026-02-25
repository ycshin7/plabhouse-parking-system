# Parking System (주차 배정 시스템)

플랩하우스 주차 자동 배정 시스템입니다.

## 구조

- **프론트엔드**: Vercel 배포 (`https://plabhouse-parking-system.vercel.app/`)
- **자동 배정**: GitHub Actions (`auto_allocate.py`) — 매일 자정(KST) 실행
- **알림**: Slack Webhook으로 배정 결과 자동 발송

## 자동 배정 흐름

1. 사용자가 웹에서 주차 신청 → `requests.json`에 저장
2. 매일 자정 GitHub Actions가 `auto_allocate.py` 실행
3. 배정 알고리즘 수행 (게스트 우선, 직원은 last_parked_date 순)
4. 결과를 `history.json`에 저장, Slack으로 알림 발송
5. `requests.json` 초기화, GitHub에 커밋/푸시

## 배정 규칙

- **관리실**: 1자리 (SUV 우선)
- **타워**: 2자리 (sante_opt_out 시 3자리)
- **우선순위**: 마지막 주차일이 오래된 순 → 신청 시간 빠른 순

## 주요 파일

| 파일 | 설명 |
|------|------|
| `auto_allocate.py` | 자동 배정 + Slack 알림 스크립트 |
| `.github/workflows/daily-allocation.yml` | GitHub Actions 스케줄러 (자정 KST) |
| `users.json` | 직원 정보 (이름, 차종, 마지막 주차일) |
| `requests.json` | 당일 주차 신청 목록 |
| `history.json` | 배정 이력 |

## GitHub Secrets 설정

| Secret | 설명 |
|--------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
