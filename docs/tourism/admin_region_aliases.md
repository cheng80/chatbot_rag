# 행정동/법정동 지역명 매칭 데이터

마지막 갱신: 2026-05-15

## 목적

사용자는 TourAPI가 요구하는 `areaCode`/`sigunguCode` 형식으로 질문하지 않는다.
`부산 중구`, `해운대 좌동`, `창원 마산합포구`, `제주시`처럼 생활권, 행정동, 법정동, 일반구 이름을 섞어 입력한다.

따라서 TourAPI 지역 코드 캐시만으로는 부족하고, 공식 행정동/법정동 데이터를 별도 매칭 데이터로 가공해 둔다.

## 원천

- 원천: 행정안전부 주민등록주소코드 `jscode20260325.zip`
- 사용 파일: `KIKmix.20260325`
- 로컬 원천 위치: `data/source/admin_regions/jscode20260325.zip`
- 처리 스크립트: `scripts/build_admin_region_aliases.py`
- 생성 결과: `data/processed/admin_region_aliases.json`

`data/source/admin_regions/`는 공식 원천을 다시 받을 수 있는 로컬 작업 폴더라 git에 넣지 않는다.
커밋 대상은 처리 스크립트와 가공 결과 JSON이다.

## 생성 방법

원천 zip이 이미 있으면:

```bash
.venv/bin/python scripts/build_admin_region_aliases.py --source-zip data/source/admin_regions/jscode20260325.zip
```

원천 zip이 없으면:

```bash
.venv/bin/python scripts/build_admin_region_aliases.py --download
```

## 현재 생성 결과

```text
source_rows=19464
sigungu_targets=228
aliases=662
dong_aliases=11467
tourapi_matched_sigungu_count=228
```

의미:

- `aliases`: 시도/시군구 단위 별칭이다. 예: `부산 중구`, `부산광역시 중구`, `중구`.
- `dong_aliases`: 행정동/법정동 단위 별칭이다. 예: `좌동`, `광복동1가`.
- `sigungu_targets`: 행안부 현행 주민등록주소코드 기준 시군구 단위다.
- `tourapi_matched_sigungu_count`: 현재 TourAPI 지역 코드 캐시와 연결된 시군구 수다.

## 서비스 연결

`TourismQueryService`는 `data/processed/tour_area_codes.json`을 먼저 읽고, 이어서 `data/processed/admin_region_aliases.json`의 `aliases`와 `dong_aliases`를 병합한다.

현재 테스트로 고정한 예외 입력:

- `부산 중구에서 휠체어 관광지 추천해줘` -> 부산 중구
- `해운대 좌동에서 유모차로 갈만한 관광지 추천` -> 부산 해운대구
- `중구에서 휠체어 타시는 아버지와 갈 관광지 추천` -> 여러 중구 후보 선택 질문
- `창원 마산합포구에서 이동약자 관광지 추천` -> 경남 창원시 TourAPI 코드
- `성남 분당구에서 무장애 관광지 추천` -> 경기 성남시 TourAPI 코드

폐지/통합된 지명은 `admin_region_aliases.json`에 의존하지 않고 코드의 레거시 예외 매핑으로 먼저 처리한다. 답변에는 사용자가 입력한 예전 이름과 현재 기준을 함께 안내한다.

- `청원군` -> 청주시
- `마산시` -> 창원시
- `진해시` -> 창원시 진해구 안내, TourAPI 조회는 창원시 기준
- `남제주군` -> 서귀포시
- `북제주군` -> 제주시

## 228, 234, 250의 차이

- `228`: 행안부 `KIKmix.20260325` 현행 행정기관/관할 법정동 기준으로 접은 시군구 수.
- `234`: 현재 `data/processed/tour_area_codes.json`의 TourAPI `areaCode2` 기준 시군구 수.
- `250`: 사용자가 실제로 지역명으로 물을 수 있는 제품 기준 목표치. 자치 시군구뿐 아니라 행정시, 일반구, 생활권 표현을 포함한다.

따라서 `admin_region_aliases.json`은 250개 제품 목표를 바로 확정하는 파일이 아니다.
다음 단계에서 이 데이터를 근거로 사용자 질문 매칭 대상 목록을 따로 선별해야 한다.

## 사용 원칙

- TourAPI 호출은 계속 TourAPI `areaCode`/`sigunguCode`를 사용한다.
- 행정동/법정동 데이터는 사용자 입력을 시도/시군구로 올려 붙이는 보조 인덱스로 쓴다.
- 동명이 지역은 바로 추천하지 말고 후보 선택을 반환한다.
- 동 단위 입력이 유일하게 한 시군구로 모이면 해당 시군구로 해석할 수 있다.
- 일반구/행정시처럼 TourAPI 시군구 체계와 어긋나는 이름은 별도 제품 대상 목록에서 결정한다.
- 폐지/통합 지명은 현재 행정구역으로 정규화하되, 답변에서 변경 사실을 숨기지 않는다.

## 예시

- `부산 중구` -> `부산` / `중구` / TourAPI `area_code=6`, `sigungu_code=15`
- `중구` -> 서울/부산/대구/인천/대전/울산 후보가 있어 선택 질문 필요
- `좌동` -> 부산 해운대구의 법정동 후보로 매칭 가능
- `창원시 마산합포구` -> 행안부 데이터에는 확인되지만 TourAPI는 창원시 단위 코드로 붙을 수 있으므로 제품 정책 결정 필요
