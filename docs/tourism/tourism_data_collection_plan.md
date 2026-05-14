# 무장애 관광 데이터 분할 수집 계획

마지막 갱신: 2026-05-15

상태: `mvp`, `fallback-1`, `fallback-2`, `fallback-3` 수집 완료.  
`data/raw/tourism_accessible` 기준 366개 Markdown, Chroma 기준 367개 문서/청크 재색인 완료.

2026-05-15 수집은 중단했다. 같은 날 추가 수집과 live UI 테스트를 하지 않는다.

## 목표

2026-06-10 전까지 앱 구현보다 먼저 기본 관광 상담 서비스를 완성한다.  
live TourAPI 조회를 기본 응답 경로로 쓰되, API 장애/쿼터/네트워크 문제에 대비해 지역별 최소 fallback Markdown을 계획적으로 확보한다.

## 원칙

- 전국을 한 번에 수집하지 않는다.
- 한 실행은 1개 배치만 담당한다.
- 기본 실행은 `--rows 20`, `--max-api-calls 300` 안에서 끝낸다.
- 수집 후에는 항상 `scripts/rebuild_index.py`와 `pytest`를 실행한다.
- API 일일 트래픽을 쓰는 작업이므로 같은 배치를 반복 실행하지 않는다.
- 외부 터널을 열어 둔 상태에서 live UI를 누르면 TourAPI 호출이 추가된다. 수집일에는 `uvicorn`과 `cloudflared` 종료 여부를 확인한다.

## 배치

| 배치 | 지역 | 목적 |
|---|---|---|
| MVP | 서울, 부산, 강릉 | 현재 데모와 회귀 테스트의 기준 데이터 |
| fallback-1 | 서울, 부산, 인천, 대전, 대구, 광주, 울산 | 동명이 시군구와 광역시 질문 방어 |
| fallback-2 | 경기, 강원, 제주, 경북, 경남 | 관광 수요가 큰 광역/도 단위 보강 |
| fallback-3 | 세종, 충북, 충남, 전북, 전남, 강릉 | 나머지 도 단위 fallback 보강 |

## 2026-05-15 수집 결과

| 배치 | 결과 |
|---|---|
| MVP | 서울/부산/강릉 각 20장 수집 |
| fallback-1 | 인천/대전/대구/광주/울산 각 20장 수집. 서울/부산은 MVP와 중복되어 재수집 생략 |
| fallback-2 | 경기/강원/제주/경북/경남 각 20장 수집. 강원은 timeout 후 단독 재시도로 성공 |
| fallback-3 | 세종/충북/충남/전북/전남/강릉 각 20장 수집 |

이 수집은 전국 전체 장소 DB 구축이 아니라, live TourAPI 실패 시 쓸 수 있는 지역별 최소 fallback 안전망이다.

### 2026-05-15 호출량 메모

수집 로그와 live UI 스모크를 기준으로 한 추정치다.

| 엔드포인트 | 추정 호출 수 | 비고 |
|---|---:|---|
| `KorWithService2/areaBasedList2` | 약 21회 | 지역별 후보 목록 |
| `KorService2/detailCommon2` | 약 386회 | 후보 공통 상세 |
| `KorWithService2/detailWithTour2` | 약 385회 | 무장애 상세 |
| 전체 합산 | 약 792회 | 엔드포인트별 1,000건이면 초과 전이나, 오늘은 중단 |

작업 종료 시점에 `uvicorn`과 `cloudflared`는 종료했다. 내일 시작 전에는 아래처럼 프로세스가 남아 있지 않은지 먼저 확인한다.

```bash
ps -ef | rg 'fetch_accessible_tourism_samples|uvicorn|cloudflared' | rg -v rg
```

### 내일 이어갈 때

이미 광역권별 최소 fallback은 확보됐으므로, 내일은 무작정 추가 수집하지 않는다.

1. `data/raw/tourism_accessible` 지역별 샘플 품질을 먼저 샘플링한다.
2. 음식점/비관광 후보가 과하게 섞였는지 확인한다.
3. 부족한 지역만 `--regions`로 좁혀 보강한다.
4. 보강 수집은 한 번에 `--max-api-calls 100` 이하로 시작한다.
5. 수집 스크립트는 `data/raw/tourism_accessible/`와 `data/generated/tour_api/live_markdown/`의 기존 `콘텐츠ID`를 먼저 읽고 중복 카드는 상세 API 호출 전에 건너뛴다. live 폴더는 질문 중 생성된 카드 캐시이고, raw 폴더는 계획 수집한 fallback/색인 후보로 본다.
6. 수집 후에는 `scripts/rebuild_index.py`와 `pytest`를 실행한다.

예시:

```bash
.venv/bin/python scripts/fetch_accessible_tourism_samples.py --regions '부족한지역1,부족한지역2' --rows 10 --max-api-calls 100
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest -q
```

내일의 우선순위는 추가 수집보다 `lookup_mode=live/indexed/sample`별 응답 품질 QA와 20문항 eval 작성이다.
전국 시군구별 최소 fallback 규모를 검토할 때는 `docs/tourism/tourism_sigungu_fallback_scale.md`를 참고한다.

## 실행 순서

```bash
.venv/bin/python scripts/fetch_tour_area_codes.py
.venv/bin/python scripts/fetch_accessible_tourism_samples.py --preset mvp --rows 20 --max-api-calls 150
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest
```

MVP 배치가 통과한 뒤 시간이 허용되는 순서대로 진행한다.

```bash
.venv/bin/python scripts/fetch_accessible_tourism_samples.py --preset fallback-1 --rows 20 --max-api-calls 300
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest

.venv/bin/python scripts/fetch_accessible_tourism_samples.py --preset fallback-2 --rows 20 --max-api-calls 300
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest

.venv/bin/python scripts/fetch_accessible_tourism_samples.py --preset fallback-3 --rows 20 --max-api-calls 300
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest
```

## 6월 10일 기준 일정

| 기간 | 목표 |
|---|---|
| 5/15-5/18 | cache/fallback 우선 응답 경로와 fallback 배치 수집 안정화 |
| 5/19-5/24 | fallback-1, fallback-2 수집 및 지역/조건 QA |
| 5/25-5/31 | fallback-3 수집, 20문항 eval, 오류/속도 보강 |
| 6/1-6/7 | 기본 서비스 고정, 웹 UI QA, 외부 터널 시연 검증 |
| 6/8-6/10 | 문서/데모 스크립트/최종 회귀 테스트 |

앱 또는 Flutter 구현은 이 일정 뒤로 둔다. 6월 10일 전에는 `/tourism/chat`, `/tourism-ui/`, Swagger, Cloudflare 터널로 기본 서비스 검증이 가능해야 한다.
