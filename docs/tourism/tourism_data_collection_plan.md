# 무장애 관광 데이터 분할 수집 계획

마지막 갱신: 2026-05-15

상태: `mvp`, `fallback-1`, `fallback-2`, `fallback-3` 수집 완료.  
중복 콘텐츠ID 정리와 시군구 fallback 확장 수집 후 `data/raw/tourism_accessible` 기준 808개 Markdown 확보.

2026-05-15 수집은 `detailCommon2` 429 응답 후 중단했다. 같은 날 추가 수집과 live UI 테스트를 하지 않는다. 실 테스트는 2026-05-16 이후 새 quota window에서 진행한다.

## 목표

2026-06-10 전까지 앱 구현보다 먼저 기본 관광 상담 서비스를 완성한다.  
live TourAPI 조회를 기본 응답 경로로 쓰되, API 장애/쿼터/네트워크 문제에 대비해 지역별 최소 fallback Markdown을 계획적으로 확보한다.

## 원칙

- 전국을 한 번에 수집하지 않는다.
- 한 실행은 1개 배치만 담당한다.
- 기본 실행은 `--rows 20`, `--max-api-calls 300` 안에서 끝낸다.
- 기본 폴백용 수집 안전치는 엔드포인트별 500건 이하로 둔다. 단, 2026-05-15에는 사용자의 명시 승인으로 하루 한도 1,000건을 기준으로 일시 확장 수집했다.
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

샘플 감사에서 중복 콘텐츠ID 16개가 확인됐다. 모두 `강릉_*`와 `강원_*`에 같은 콘텐츠ID가 함께 있는 형태였다. 도 단위 `강원` 수집 결과에 강릉 장소가 포함되고, 별도 `강릉` 특화 수집도 수행되면서 생긴 중복이다. 정리 기준은 더 구체적인 `강릉_*` 파일을 canonical fallback으로 보존하고 중복 `강원_*` 파일 16개를 제거하는 것이다. 정리 후 파일명 기준 `강원` 샘플은 4개로 줄었지만, 제거된 중복 장소는 `강릉_*` 파일과 주소의 `강원특별자치도 강릉시` 정보로 보존된다. 강릉 외 강원 지역 커버리지가 필요하면 다음 수집에서 `--regions 강원`으로 좁게 보강한다. 현재 수집 스크립트는 기존 raw/live Markdown의 콘텐츠ID를 먼저 읽고 동일 ID를 상세 API 호출 전에 건너뛰도록 보강했다. 다음 수집 전에는 `scripts/audit_tourism_samples.py --fail-on-duplicates`로 중복 증가 여부를 확인한다.

### 2026-05-15 호출량 메모

수집 로그와 live UI 스모크를 기준으로 한 추정치다.

| 엔드포인트 | 추정 호출 수 | 비고 |
|---|---:|---|
| `KorWithService2/areaBasedList2` | 약 21회 | 지역별 후보 목록 |
| `KorService2/detailCommon2` | 약 386회 | 후보 공통 상세 |
| `KorWithService2/detailWithTour2` | 약 385회 | 무장애 상세 |
| 안전치 대비 남은 수량 | areaBased 약 479 / detailCommon 약 114 / detailWithTour 약 115 | 엔드포인트별 500건 안전치 기준 |

### 2026-05-15 시군구 fallback 1차 부분 수집

FastAPI 서버와 Cloudflare 터널을 끈 뒤, 엔드포인트별 500건 안전치에서 오늘 이미 사용한 호출량을 차감하고 수집했다.

```bash
.venv/bin/python scripts/fetch_accessible_tourism_samples.py --sigungu-fallback --cards-per-sigungu 3 --rows 20 --daily-endpoint-budget 500 --used-area-based 22 --used-detail-common 388 --used-detail-with-tour 387
```

결과:

| 항목 | 결과 |
|---|---:|
| 추가 실행 `areaBasedList2` | 48회 |
| 추가 실행 `detailCommon2` | 112회 |
| 추가 실행 `detailWithTour2` | 112회 |
| Markdown 총량 | 460개 |
| 감사 결과 | 파싱 실패 0, 중복 0, 필수 필드 누락 0 |
| Chroma 재색인 | 461개 문서 / 463개 청크 |
| TourAPI 지역 코드 234개 중 3장 이상 확보 | 90개 시군구 |
| 3장 목표까지 남은 부족분 | 약 365장 |

실패한 첫 시도에서 이미 발생한 호출까지 보수적으로 포함하면 2026-05-15 누적 추정치는 `areaBasedList2` 약 70회, `detailCommon2` 약 500회, `detailWithTour2` 약 499회다. 폴백 수집 안전치인 엔드포인트별 500건 이내에서 멈췄으므로 같은 날 추가 수집은 하지 않는다.

### 2026-05-15 시군구 fallback 확장 수집

사용자 승인으로 이날만 엔드포인트별 500건 안전치를 일시적으로 풀고, 공공데이터포털의 엔드포인트별 일일 1,000건 한도 안에서 폴백 카드 확보를 우선했다.

```bash
.venv/bin/python scripts/fetch_accessible_tourism_samples.py --sigungu-fallback --cards-per-sigungu 3 --rows 20 --daily-endpoint-budget 1000 --used-area-based 70 --used-detail-common 500 --used-detail-with-tour 499
```

이후 추가 이어받기 실행 중 `detailCommon2`가 429를 반환해 수집을 즉시 중단했다. 같은 날 더 호출하지 않는다.

결과:

| 항목 | 결과 |
|---|---:|
| Markdown 총량 | 643개 |
| 추가 확보 | 183개 |
| 감사 결과 | 파싱 실패 0, 중복 0, 필수 필드 누락 0 |
| TourAPI 지역 코드 234개 중 3장 이상 확보 | 161개 시군구 |
| 234개 기준 3장 목표까지 남은 부족분 | 약 182장 |

추가로 수집 스크립트는 TourAPI가 빈 결과를 `items: ""`처럼 반환하는 경우와 429 같은 `TourAPIError`를 만나도 전체 실행이 비정상 종료되지 않고 요약을 남기도록 보강했다.

주의: 현재 수집 스크립트의 대상은 `data/processed/tour_area_codes.json`의 TourAPI 지역 코드 234개다. 사용자가 말한 전국 실사용 지역 250개 기준에는 행정시/일반구 등 보강 대상이 더 포함될 수 있으므로, 다음 단계에서 대상 목록을 확장해야 한다.

### 2026-05-16 시군구 fallback 이어받기 수집

새 quota window에서 평시 안전치인 엔드포인트별 500건 기준으로 남은 시군구 fallback을 이어받았다.

```bash
.venv/bin/python scripts/fetch_accessible_tourism_samples.py --sigungu-fallback --cards-per-sigungu 3 --rows 20 --daily-endpoint-budget 500
```

결과:

| 항목 | 결과 |
|---|---:|
| 추가 실행 `areaBasedList2` | 73회 |
| 추가 실행 `detailCommon2` | 167회 |
| 추가 실행 `detailWithTour2` | 167회 |
| Markdown 총량 | 808개 |
| 감사 결과 | 파싱 실패 0, 중복 0, 필수 필드 누락 0 |
| Chroma 재색인 | 809개 문서 / 816개 청크 |
| TourAPI 지역 코드 234개 중 3장 이상 확보 | 228개 시군구 |
| 0장 지역 | 청원군, 마산시, 진해시, 남제주군, 북제주군 |
| 3장 미만 지역 | 계룡시 1장 |

0장 지역 5개는 폐지/통합된 행정구역명으로 본다. 사용자 질문에서는 예전 이름을 그대로 실패 처리하지 않고 현재 행정구역명을 안내한 뒤 현재 지역 기준으로 찾는다.

| 예전 입력 | 현재 안내/조회 기준 |
| --- | --- |
| 청원군 | 청주시 |
| 마산시 | 창원시 |
| 진해시 | 창원시 진해구 안내, TourAPI 조회는 창원시 기준 |
| 남제주군 | 서귀포시 |
| 북제주군 | 제주시 |

계룡시 1장은 폐지 지명이 아니라 실제 저커버리지 지역으로 보고, 필요하면 다음 수집에서 별도 보강한다.

작업 종료 시점에 `uvicorn`과 `cloudflared`는 종료했다. 내일 시작 전에는 아래처럼 프로세스가 남아 있지 않은지 먼저 확인한다.

```bash
ps -ef | rg 'fetch_accessible_tourism_samples|uvicorn|cloudflared' | rg -v rg
```

### 다음 quota window에서 이어갈 때

이미 광역권별 MVP 최소 fallback과 시군구 fallback 확장 수집은 진행됐다. 다만 전국/주요 시군구 fallback은 아직 완성 전이며 별도 확장 작업으로 남아 있다.

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

다음 우선순위는 0장/1장 지역의 행정구역 유효성을 확인하고, `lookup_mode=live/indexed/sample`별 응답 품질 QA와 확장 eval을 실행하는 것이다.
전국 시군구별 최소 fallback 규모를 검토할 때는 `docs/tourism/tourism_sigungu_fallback_scale.md`를 참고한다. 평시에는 엔드포인트별 500건 안전치 안에서 분할 실행하고, 예외적으로 1,000건 한도를 쓸 때도 429가 나오면 즉시 멈춘다.

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
