# ticket_watcher

SHIBUYA SKY (Webket) 예약 슬롯 자동 감시. GitHub Actions cron으로 5분마다 페이지를 확인하고, 조건에 맞는 슬롯이 새로 열리면 Discord 채널로 알림.

## 감시 조건

- 2026-05-25 — 시간 무관
- 2026-05-26 — 20:20 이후 시작 슬롯만
- 2026-05-27 — 20:20 이후 시작 슬롯만

매진(×, status=`00`) 슬롯은 제외. 직전 실행 대비 **새로 열린** 슬롯만 알림.

## 셋업

1. Repo `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. Name: `DISCORD_WEBHOOK`, Value: Discord 웹훅 URL
3. `Actions` 탭에서 `Watch ticket availability` 워크플로우 활성화
4. (선택) `Run workflow` 버튼으로 즉시 테스트 가능

## 종료

10일 정도 운영 후 정리 시:
- `Settings` → `Actions` → Disable Actions, 또는
- 그냥 repo 삭제

## 파일

- `ticket_watcher.py` — 1회 실행용 파이썬 스크립트
- `.github/workflows/watch.yml` — 5분 cron 워크플로우
- `last_state.json` — 직전 실행 결과 (자동 갱신, 커밋됨)
