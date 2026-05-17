# 관광 챗봇 데이터 원본 출처 정리

마지막 갱신: 2026-05-17

이 문서는 가공 후 파일이 아니라, 프로젝트에서 실제로 사용했거나 실험 검토한 **원본 데이터 출처**를 기준으로 정리한다. 학습에 들어간 데이터, 평가 전용 데이터, 런타임 추천 근거 데이터를 구분한다.

## 요약

| 구분 | 원본 출처 | 프로젝트 내 용도 | 런타임 사용 |
|---|---|---|---|
| 관광지/접근성 카드 | 한국관광공사 TourAPI 국문 관광정보, 무장애 여행 정보 | 추천 카드, RAG/fallback, live 조회 | 사용 |
| 일반/확장 관광 후보 | 한국관광공사 중심 관광지, 연관 관광지, 웰니스 관광정보 | 무장애 카드 부족 지역의 후보 풀 확대 검토 | 도입 준비 |
| 상가/카페 후보 | 소상공인시장진흥공단 상가(상권)정보 API | 카페, 베이커리, 음식점, 상점 후보 풀 확대 | 수집 테스트 완료 |
| 전국 관광지 표준 후보 | 전국관광지정보표준데이터 | TourAPI 외 표준 관광지 후보 보강 | 로컬 JSON 확보 |
| 전국 편의시설 근거 | 전국장애인편의시설표준데이터 | 일반 후보에 접근성 근거 매칭 | 목록/상세 smoke 완료 |
| 일반음식점 인허가 | 행정안전부/지자체 전국 일반음식점 표준데이터 | 지역별 음식점 존재/커버리지 진단, 후보 검증 보조 | 추천 후보 제외 |
| 관광 수요 지표 | 한국관광공사 지역별 관광 자원 수요 | 지역/카테고리 랭킹 보정 검토 | 수집 테스트 완료 |
| 지역 코드 | 한국관광공사 TourAPI `areaCode2` | 광역/시군구 코드 캐시 | 사용 |
| 관광 빅데이터 행정 코드 | 한국관광공사 TourAPI 관광지 시군구 코드 엑셀 | 중심/연관/수요 API용 `areaCd`, `signguCd` 매핑 | 도입 준비 |
| 행정동/법정동 | 행정안전부 주민등록주소코드 | 사용자 지역명 alias, 법정동/행정동 보정 | 사용 |
| 법정동 기준 시군구 단위 엑셀 | 사용자 제공 교차 확인 자료 | 제품 표현 수와 현행 행정구역 교차 확인 | 직접 사용 안 함 |
| AI Hub 대화 데이터 | AI Hub 목적대화/한국어 대화/웰니스 대화 | 의도 분류 학습/holdout 일부 | 가공 모델만 사용 |
| Hugging Face 공개 데이터셋 | CLINC150-KO, kor_3i4k, KoSGD 등 | 의도 분류 실험 후보 | 기본 학습 제외 |
| Gemini 생성 holdout | Gemini API 생성/검수 | 의도 분류 독립 평가 | 학습 제외 |
| Codex/LLM 생성 문맥 데이터 | Codex/LLM 생성 + 자동 검증 | 문맥 라벨 보강, noisy 입력 평가 | 가공 모델/검증셋 사용 |
| 자체 제작 평가셋 | 프로젝트 내부 작성/생성 | chat 품질, adversarial, rotating blind 평가 | 학습/평가 분리 |

## 1. 관광 추천 근거 데이터

### 한국관광공사 TourAPI

원본 출처:

- 공공데이터포털 `한국관광공사_국문 관광정보 서비스_GW`
- 공공데이터포털 `한국관광공사_무장애 여행 정보`
- 기본 관광정보 API: `https://apis.data.go.kr/B551011/KorService2`
- 무장애 여행 정보 API: `https://apis.data.go.kr/B551011/KorWithService2`

사용한 주요 엔드포인트:

| 엔드포인트 | 용도 |
|---|---|
| `KorWithService2/areaCode2` | 광역/시군구 지역 코드 수집 |
| `KorWithService2/areaBasedList2` | 지역별 무장애 관광 후보 조회 |
| `KorService2/searchKeyword2` | 부족 지역 보강 후보 검색 |
| `KorService2/detailCommon2` | 관광지 공통 상세 정보 조회 |
| `KorWithService2/detailWithTour2` | 휠체어, 주차, 화장실, 수유실 등 무장애 상세 근거 조회 |

프로젝트 산출물:

| 파일/폴더 | 설명 |
|---|---|
| `data/processed/tour_area_codes.json` | TourAPI `areaCode2` 기준 지역 코드 캐시 |
| `data/raw/tourism_accessible/` | TourAPI 상세를 Markdown 카드로 저장한 fallback/RAG 원천 |
| `data/generated/tour_api/live_markdown/` | live 조회 중 저장된 지역별 Markdown 캐시 |

현재 수량:

| 항목 | 수량 |
|---|---:|
| raw fallback Markdown | 904개 |
| live Markdown cache | 76개 |
| TourAPI 시군구 코드 | 234개 |
| 공식 무장애 상세 3장 이상 확보 | 228개 시군구 |
| 공식 무장애 상세 3장 미만 | 계룡시 1장 |

주의:

- TourAPI 상세와 무장애 상세에서 확인된 근거만 추천 카드에 사용한다.
- 일반 관광 검색 결과라도 `detailWithTour2`에 무장애 상세가 없으면 접근성 카드로 편입하지 않는다.
- 한국관광공사 열린관광 상세 URL은 콘텐츠 ID만으로 안정적 공개 링크를 만들 수 없어 UI에서는 추정 링크를 숨기고 출처명/지도 검색 중심으로 제공한다.

### 한국관광공사 후보 풀 확장 API

현재 무장애 여행 정보만으로는 시군구별 후보 폭이 좁다. 예를 들어 성남시는 로컬 무장애 카드가 도서관, 갤러리, 호텔 중심으로만 확보되어 사용자가 `성남시 식당`처럼 일반 장소 유형을 묻는 경우 후보 부족이 발생한다. 이를 보완하기 위해 아래 한국관광공사 API를 후보 풀 확장 레이어로 검토했다.

원본 출처:

| 데이터 | 공공데이터포털 항목 | 서비스 ID | 주요 용도 | 런타임 상태 |
|---|---|---|---|---|
| 기초지자체 중심 관광지 정보 | `한국관광공사_기초지자체 중심 관광지 정보` | `LocgoHubTarService1` | 시군구별 중심 관광지 100위 후보 확보 | 도입 준비 |
| 관광지별 연관 관광지 정보 | `한국관광공사_관광지별 연관 관광지 정보` | `TarRlteTarService1` | 중심 관광지와 연관된 관광지/음식/숙박 후보 확보 | 도입 준비 |
| 지역별 관광 자원 수요 | `한국관광공사_지역별 관광 자원 수요` | `AreaTarResDemService` | 지역별 관광 서비스/문화 자원 수요 지표로 랭킹 보정 | 미사용 |
| 웰니스 관광정보 | `한국관광공사_웰니스관광정보` | `WellnessTursmService` | 힐링, 스파, 푸드, 스테이 등 테마 후보 보강 | 도입 준비 |

확인한 주요 오퍼레이션:

| 서비스 | 오퍼레이션 | 용도 |
|---|---|---|
| `LocgoHubTarService1` | `areaBasedList1` | 지역기반 중심 관광지 정보 조회 |
| `TarRlteTarService1` | `areaBasedList1` | 지역기반 관광지별 연관 관광지 정보 조회 |
| `TarRlteTarService1` | `searchKeyword1` | 키워드 기반 관광지별 연관 관광지 정보 조회 |
| `AreaTarResDemService` | `areaTarSvcDemList` | 지역별 관광 서비스 수요 정보 조회 |
| `AreaTarResDemService` | `areaCulResDemList` | 지역별 문화 자원 수요 정보 조회 |
| `WellnessTursmService` | `ldongCode` | 웰니스 API용 법정동 코드 조회 |
| `WellnessTursmService` | `areaBasedList` | 지역기반 웰니스 관광정보 조회 |
| `WellnessTursmService` | `searchKeyword` | 키워드 기반 웰니스 관광정보 조회 |
| `WellnessTursmService` | `detailCommon`, `detailIntro`, `detailInfo`, `detailImage` | 웰니스 상세/이미지 조회 |

로컬 원천 문서:

| 폴더 | 내용 |
|---|---|
| `data/source/tourapi_guides/hub/` | 중심 관광지 API 활용매뉴얼, 시군구 코드 엑셀 |
| `data/source/tourapi_guides/related/` | 연관 관광지 API 활용매뉴얼, 시군구 코드 엑셀 |
| `data/source/tourapi_guides/demand/` | 지역별 관광 자원 수요 API 활용매뉴얼, 시군구 코드 엑셀 |
| `data/source/tourapi_guides/wellness/` | 웰니스 관광정보 활용매뉴얼 |
| `data/processed/tourapi_bigdata_region_codes.json` | 중심/연관/수요 API용 `areaCd`, `signguCd` 매핑 캐시 |
| `data/generated/tour_api/external_source_smoke_latest.json` | 신규 외부 API 수집 smoke 결과 |

중요한 차이:

- 기존 무장애/국문 TourAPI는 `areaCode`, `sigunguCode`를 사용한다.
- 중심 관광지, 연관 관광지, 지역별 관광 자원 수요 API는 `areaCd`, `signguCd`를 사용한다.
- ZIP 안의 `한국관광공사_TourAPI_관광지_시군구_코드정보_v1.0.xlsx`가 이 매핑의 기준이다.
- 예: 문서 예시는 `areaCd=11`, `signguCd=11530`처럼 법정동/행정구역 계열 코드를 사용한다.
- 성남시, 수원시처럼 일반구가 있는 도시는 새 API에서 `성남시 분당구`, `성남시 수정구`처럼 여러 `signguCd`로 나뉜다. 따라서 `성남시` 질의는 `region_group_index`에서 복수 `signguCd`로 확장해 조회해야 한다.

적용 원칙:

- 이 API들은 접근성 근거 API가 아니라 일반 후보/수요 확장 API다.
- 후보를 추천 카드에 넣더라도 `detailWithTour2` 또는 기존 무장애 카드와 매칭되지 않으면 `접근성 확인 필요` 등급으로 표시한다.
- 사용자가 휠체어, 장애인 화장실, 수어, 점자 등 명시적 접근성 조건을 말하면 접근성 근거 없는 일반 후보를 조건 충족 카드처럼 보여주지 않는다.
- 사용자가 `성남시 식당`, `실내 카페`처럼 지역과 장소 유형만 말하면 일반 후보 확장을 허용할 수 있다.

수집 smoke 결과:

| API | 테스트 지역/조건 | 결과 | 해석 |
|---|---|---|---|
| 중심 관광지 `areaBasedList1` | 성남시 수정구/중원구/분당구, `baseYm=202504` | 구별 3건씩 정상 응답 | 후보 풀 확장에 바로 사용할 수 있다. |
| 연관 관광지 `areaBasedList1` | 성남시 수정구/중원구/분당구, `baseYm=202504` | 구별 3건씩 정상 응답 | 중심 관광지 기반 주변 후보 확장에 사용할 수 있다. |
| 지역별 관광 자원 수요 `areaTarSvcDemList` | 성남시 수정구, `baseYm=202509`, 쇼핑유형 지표 | 1건 정상 응답 | 카드 후보 자체가 아니라 지역/카테고리 랭킹 보정 지표로 사용한다. |
| 웰니스 `areaBasedList` | 경기도/성남시 수정구, 음식 content type | 정상 응답, 샘플 0건 | 지역/테마별 데이터 유무가 갈린다. 후보 확장 전 별도 커버리지 점검이 필요하다. |

주의:

- 중심/연관/수요 API는 `baseYm`이 필수다. 매뉴얼 예시 기준으로 중심/연관은 `202504`, 수요는 `202509`가 정상 응답을 확인했다.
- 성남시처럼 일반구가 있는 지역은 단일 코드가 아니라 복수 `signguCd` 조회가 필요하다.

### 전국 단위 일반 후보/편의시설 데이터

무장애 TourAPI만으로는 지역별 후보 폭이 좁기 때문에 전국 단위 일반 후보와 접근성 근거 데이터를 별도 레이어로 추가 검토한다.

| 데이터 | 원본 출처 | 프로젝트 상태 | 용도 |
|---|---|---|---|
| 전국장애인편의시설표준데이터 | 공공데이터포털 `전국장애인편의시설표준데이터` | 목록/상세 API smoke 성공 | 일반 후보에 경사로, 승강기, 점자블록, 장애인 화장실 등 접근성 근거 매칭 |
| 소상공인시장진흥공단 상가(상권)정보 API | 공공데이터포털 `소상공인시장진흥공단_상가(상권)정보_API` | 행정동 코드/음식점 조회 smoke 성공 | 카페, 음식점, 베이커리, 상점 등 영업 중 업소 후보 확장 |
| 전국관광지정보표준데이터 | 공공데이터포털 `전국관광지정보표준데이터` | 로컬 JSON 원천 확보, 854 records | TourAPI 외 표준 관광지 후보 확장 |
| 전국 일반음식점 표준데이터 | 공공데이터포털/행정안전부 `일반음식점` | 로컬 원천 삭제 | 인허가성 데이터라 관광 추천 후보 매칭에 사용하지 않음 |

로컬 원천 파일:

| 파일 | 설명 |
|---|---|
| `data/source/public_tourist_standard/national_tourist_standard.json` | 전국관광지정보표준데이터 JSON. 854 records. 전체 관광지/상점/음식점을 포괄하는 데이터가 아니라 표준 관광지 데이터로 제한한다. |
| `data/source/accessibility_facilities/disabled_facility_technical_doc_20241224.docx` | 장애인편의시설 API 기술문서. `getDisConvFaclList`, `getFacInfoOpenApiJpEvalInfoList` 명세 포함. |
| `data/source/sbiz_store/openapi_guide/` | 소상공인 상가정보 API 활용가이드, 업종분류 엑셀. 주요상권 CSV는 직접 사용하지 않아 로컬 원천에서 제거. |

삭제한 로컬 원천:

| 파일 | 삭제 사유 |
|---|---|
| `data/source/food/general_restaurants.csv` | 약 659MB 대용량 인허가성 일반음식점 CSV. 관광 추천 후보 매칭에 부적합하고 Git 반입 불가. |
| `data/source/sbiz_store/openapi_guide/소상공인시장진흥공단_주요상권현황_20240101.csv` | 상권 현황 원본 CSV. 현재 런타임/평가/후보 매칭에 직접 사용하지 않음. |

전국관광지정보표준데이터 확인 사항:

- 파일명은 `전국관광지정보표준데이터`지만 전국의 모든 관광 자원 전체 목록은 아니다.
- 현재 확보한 JSON은 854건이며 관광지명, 구분, 주소, 위경도, 공공편익시설, 주차, 소개, 관리기관 등을 담는다.
- 성남시 주소 기준 매칭은 0건이다. 따라서 성남시 음식점/카페 후보 부족 문제를 직접 해결하는 데이터로 보기 어렵다.
- 용도는 TourAPI 외 공공 표준 관광지 후보를 보강하는 제한적 레이어로 둔다.

일반음식점 CSV 확인 사항:

- 주요 컬럼: `사업장명`, `업태구분명`, `영업상태명`, `상세영업상태명`, `도로명주소`, `지번주소`, `전화번호`, `좌표정보(X)`, `좌표정보(Y)`.
- 원본 좌표는 문서상 Bessel 중부원점TM 계열일 가능성이 있어 위경도 변환 검증이 필요하다.
- 폐업 행이 포함되어 있으므로 `영업상태명=영업` 또는 `상세영업상태명=영업` 계열만 후보로 사용한다.
- 인허가 데이터는 관광 적합도, 영업 품질, 접근성, 방문 적합성을 설명하지 않는다.
- 따라서 런타임 추천 후보로 직접 편입하지 않는다.
- 용도는 지역별 음식점 존재/밀도 진단, 다른 API에서 들어온 식당 후보의 인허가 보조 검증, 데이터 커버리지 설명으로 제한한다.

도입 우선순위:

1. `전국장애인편의시설표준데이터` 수집 및 주소/명칭 정규화.
2. 소상공인 상가정보 API로 카페/베이커리/상점 후보 보강.
3. 전국관광지정보표준데이터로 일반 관광지 후보 보강.
4. 일반음식점 인허가 CSV는 추천 후보가 아니라 검증/분석 보조 인덱스로만 가공.

수집 smoke 결과:

| API | 결과 | 다음 확인 |
|---|---|---|
| 전국관광지정보표준데이터 | 로컬 JSON 854건 확인, 성남시 매칭 0건 | 전국 전체 관광지 데이터로 과대 해석하지 않고 표준 관광지 후보로만 사용 |
| 소상공인 행정동 코드 | `baroApi?resId=dong&catId=admi&signguCd=41131` 정상, 17건 | 성남시 3개 구 전체 행정동 순회 수집 필요 |
| 소상공인 음식점 | `storeListInDong?divId=adongCd&key=41131510&indsLclsCd=I2` 정상, 샘플 3건 | 기존 `signguCd` 직접 조회는 잘못된 파라미터였으므로 행정동 단위로 수집 |
| 장애인편의시설 목록 | `getDisConvFaclList?siDoNm=경기도&cggNm=성남시` 정상, total 2399건 | 좌표 0값이 포함되어 주소/명칭 기반 매칭 보정 필요 |
| 장애인편의시설 상세 | `getFacInfoOpenApiJpEvalInfoList` 정상 | 목록의 `wfcltId`로 상세 편의시설 근거를 후속 수집 |

## 2. 지역명/행정구역 데이터

### 한국관광공사 지역 코드

원본 출처:

- TourAPI `KorWithService2/areaCode2`

용도:

- 추천 API 호출 단위인 `areaCode`, `sigunguCode` 확정
- 사용자가 광역/시군구를 말했을 때 TourAPI 호출 코드로 변환

프로젝트 산출물:

- `data/processed/tour_area_codes.json`

### 행정안전부 주민등록주소코드

원본 출처:

- 행정안전부 주민등록주소코드
- 로컬 원천 작업 파일: `data/source/admin_regions/jscode20260325.zip`

가공:

- 스크립트: `scripts/build_admin_region_aliases.py`
- 산출물: `data/processed/admin_region_aliases.json`

용도:

- `해운대 좌동`, `창원 마산합포구`, `성남 분당구`처럼 TourAPI가 직접 받지 않는 생활권/일반구/행정동/법정동 표현을 시군구 후보로 올려 붙인다.
- 과거 지명은 코드의 예외 매핑으로 현재 행정구역 기준 안내를 제공한다.

관련 문서:

- `docs/tourism/admin_region_aliases.md`

### 법정동 기준 시군구 단위 엑셀

원본 출처:

- 사용자 제공 엑셀: `법정동 기준 시군구 단위.xlsx`

용도:

- TourAPI 234개, 행안부 현행 시군구 alias 228개, 제품 표현 상한 250개 사이의 차이를 교차 확인했다.
- 런타임 데이터로 직접 넣은 파일은 아니며, 행정구역 수 해석과 일반구/행정시 표현 정책을 점검하는 참고 자료로 사용했다.

## 3. 의도 분류 데이터

의도 분류는 사용자의 다음 행동을 분류한다. 예: 추천, 더 보기, 최신 조회, 조건 추가, 조건 교체, 지역 변경, 출처 질문, 미지원 요청.

### 프로젝트 자체 seed/generated 발화

원본 출처:

- 프로젝트 내부 작성 seed 문장
- deterministic generator로 만든 변형 문장

파일:

| 파일 | rows | 용도 |
|---|---:|---|
| `data/eval/tourism_intent_seed_utterances.jsonl` | 163 | seed 발화 |
| `data/eval/tourism_intent_generated_utterances.jsonl` | 13,200 | 생성 변형 발화 |

### AI Hub

원본 출처:

- AI Hub `용도별 목적대화 데이터`
- AI Hub `한국어 대화`
- AI Hub `웰니스 대화 스크립트 데이터셋`

로컬 원천 위치:

- `data/external/aihub/raw/`

가공:

- 스크립트: `scripts/extract_aihub_tourism_intent_utterances.py`
- 고신뢰 규칙으로 `recommend_places`, `add_condition`, `unsupported_request` 일부만 추출했다.

산출물:

| 파일 | rows | 용도 |
|---|---:|---|
| `data/eval/tourism_intent_aihub_utterances.jsonl` | 2,700 | 의도 분류 학습 후보 |
| `data/eval/tourism_intent_aihub_holdout.jsonl` | 497 | 학습 제외 독립 holdout |

주의:

- AI Hub 원본 전체를 그대로 학습에 넣지 않았다.
- 관광 챗봇 taxonomy에 맞는 고신뢰 발화만 약한 규칙으로 재라벨링했다.
- AI Hub validation split은 독립 holdout으로 분리한다.

### Hugging Face 공개 데이터셋

원본 출처:

- `neuralfoundry-coder/clinc150-ko`
- `wicho/kor_3i4k`
- `AIWORKX/KoSGD`

가공:

- 스크립트: `scripts/fetch_tourism_intent_external_utterances.py`
- 산출물: `data/eval/tourism_intent_external_utterances.jsonl`

현재 수량:

| 파일 | rows | 런타임 채택 |
|---|---:|---|
| `data/eval/tourism_intent_external_utterances.jsonl` | 9,108 | 기본 학습 제외 |

판단:

- taxonomy 재라벨링 없이 섞으면 AI Hub/adversarial holdout 성능이 떨어져 기본 런타임 학습에는 넣지 않는다.
- 실험/재라벨링 후보로만 둔다.

### Gemini independent holdout

원본 출처:

- Gemini API `gemini-2.5-flash`

가공:

- 생성: `scripts/generate_tourism_intent_gemini_holdout.py`
- 2차 검수: `scripts/verify_tourism_intent_gemini_holdout.py`

산출물:

| 파일 | rows | 용도 |
|---|---:|---|
| `data/eval/tourism_intent_gemini_holdout.jsonl` | 770 생성본 | raw 생성본 |
| `data/eval/tourism_intent_gemini_holdout_verified.jsonl` | 676 | 평가/문제 탐색 전용 |

주의:

- 사람 작성 holdout이 아니므로 학습셋에 넣지 않는다.
- rule override 보강 전/후 비교와 약점 탐색에만 사용한다.
- 신규 AI-generated holdout은 기존 Gemini 파일과 섞지 않는다.

### 의도 분류 최종 학습셋

산출물:

| 파일 | rows | 설명 |
|---|---:|---|
| `data/processed/tourism_intent_training.jsonl` | 16,254 | seed/generated + AI Hub 고신뢰 추출 발화 기반 학습셋 |

## 4. 문맥 라벨 데이터

문맥 라벨은 자연어 조건의 의미를 해석한다. 예: strict AND, soft AND, OR, 조건 추가, 조건 교체, 조건 제외, 가족 맥락, 이동성 맥락, 필수 시설 근거.

### 자체 생성 hard/context 데이터

원본 출처:

- 프로젝트 내부 generator
- 문맥 라벨 정의에 맞춰 deterministic하게 생성한 문장

파일:

| 파일 | rows | 용도 |
|---|---:|---|
| `data/processed/tourism_context_training.jsonl` | 4,400 | 기본 문맥 학습셋 |
| `data/eval/tourism_context_hard_holdout.jsonl` | 4,800 | locked hard holdout |
| `data/eval/tourism_context_specific_facility_adversarial_holdout.jsonl` | 980 | 시설 근거 경계 평가 |

주의:

- 생성형 경계셋은 같은 파일을 보고 보강하면 최종 품질 점수로 쓰지 않는다.
- 1.0000이 반복되는 focused/contract 셋은 “완성”이 아니라 반례 부족 신호로 본다.

### Codex/LLM hard-style, noisy 문맥 데이터

원본 출처:

- Codex/LLM 생성 발화
- 프로젝트 validator로 schema, 라벨, 중복, 기존 train/holdout overlap 검증

가공:

- 프롬프트 생성: `scripts/build_tourism_context_llm_generation_prompt.py`
- deterministic noisy seed 생성: `scripts/generate_tourism_context_human_light_seed.py`
- 검증 파이프라인: `scripts/run_tourism_context_human_light_pipeline.py`
- 검증기: `scripts/validate_tourism_context_llm_dataset.py`

산출물:

| 파일/폴더 | rows | 용도 |
|---|---:|---|
| `data/processed/tourism_context_llm_hard_training_20260517_human_light_1000.valid.jsonl` | 1,000 | noisy 문맥 학습/검증 후보 |
| `data/processed/tourism_context_llm_hard_training_20260518_human_light_5000.valid.jsonl` | 5,000 | 스타일/어투/오타/문맥 경계를 확장한 hard-style 문맥 후보 |
| `data/processed/context_runtime_20260517_human_light_1000/` | train 5,400 / test 4,800 | 런타임 문맥 모델 재학습 split |
| `data/processed/context_finetune_20260517_human_light_1000/` | train/validation/test | Transformer 후보 실험 split |

특징:

- 사람이 대량 검수하기 어려운 전제를 반영해 human-light 자동 검증을 사용한다.
- 원문 품질이 낮은 실제 입력을 반영하기 위해 무띄어쓰기, 부분 띄어쓰기 붕괴, 축약/오타, 구어체 tail을 일부 포함한다.
- 정규화 레이어가 원문을 버리지 않고 `raw_query`, `normalized_query`, `rewrite_query`를 함께 남기도록 했다.

2026-05-18 5,000건 확장:

| 파일 | rows | 비고 |
|---|---:|---|
| `data/generated/tour_api/context_llm_prompts/context_llm_generation_prompt_20260518_5000.md` | - | GPT에 줄 5,000건 hard-style 생성 프롬프트 |
| `data/generated/tour_api/context_llm_batches/context_llm_batch_20260518_human_light_5000.raw.jsonl` | 5,000 | deterministic GPT-style seed 원본 |
| `data/processed/tourism_context_llm_hard_training_20260518_human_light_5000.valid.jsonl` | 5,000 | schema/라벨/중복 검증 통과 |
| `data/generated/tour_api/context_llm_reports/context_human_light_report_20260518_human_light_5000.json` | - | rule/current classifier 자동 감사 |
| `data/generated/tour_api/context_llm_reports/context_human_light_review_queue_20260518_human_light_5000.jsonl` | 3,597 | 현재 rule/classifier와 불일치하는 검토 큐 |

5,000건 확장 감사 결과:

| 평가 | exact | micro-F1 | mismatch | high-risk mismatch |
|---|---:|---:|---:|---:|
| rule-only | 0.2830 | 0.6587 | 3,585 | 2,357 |
| current context classifier | 0.2834 | 0.6620 | 3,583 | 2,346 |

해석:

- 이 5,000건은 현재 규칙에 잘 맞는 쉬운 문장 모음이 아니라, 실패/경계 검토 후보를 많이 포함한 학습 후보 집합이다.
- 같은 파일로 성능 개선을 주장하지 않는다. 학습에 사용한 뒤에는 새 blind set과 실제 `/tourism/chat` 카드 평가로만 채택 여부를 본다.
- review queue가 크므로 전체를 바로 런타임에 반영하지 않고, 라벨/문맥 bucket별로 분리해 사용한다.

## 5. 실제 chat 평가셋

원본 출처:

- 프로젝트 내부에서 실제 `/tourism/chat` 응답을 채점하기 위해 작성한 질문/대화 시나리오

대표 파일:

| 파일 | 용도 |
|---|---|
| `data/eval/tourism_20_questions.jsonl` | 초기 기본 질문 |
| `data/eval/tourism_80_questions.jsonl` | 확장 질문 |
| `data/eval/tourism_100_questions.jsonl` | 100문항 평가 |
| `data/eval/tourism_challenge_questions.jsonl` | 챌린지 질문 |
| `data/eval/tourism_conversation_challenge.jsonl` | 대화형 챌린지 |
| `data/eval/tourism_expanded_conversation_challenge.jsonl` | 확장 대화형 챌린지 |
| `data/eval/tourism_change_replace_chat_holdout.jsonl` | 조건 교체/지역 변경 멀티턴 평가 |
| `data/eval/tourism_adversarial_chat_holdout.jsonl` | adversarial chat 평가 |
| `data/eval/tourism_context_blind_chat_eval.jsonl` | 문맥 blind chat 평가 |
| `data/eval/tourism_context_blind_chat_eval_v2.jsonl` | 확장 문맥 blind chat 평가 |
| `data/eval/tourism_noisy_chat_eval_20260517.jsonl` | 오타/무띄어쓰기/모호 지역 noisy chat 평가 |
| `data/eval/tourism_context_rotating_blind_holdout_20260517_v5.jsonl` | soft/add/exclude 경계 확인용 rotating blind |

용도:

- 의도/문맥 라벨 점수가 아니라 실제 카드 추천, 부족 안내, 더 보기, 출처 표시가 맞는지 확인한다.
- 모델 채택 여부는 단순 label score보다 실제 `/tourism/chat` 카드 품질 평가를 우선한다.
- 의미가 모호한 입력은 임의로 지역/조건을 확정하지 않고 clarification으로 추가 질의하는지 확인한다.

## 6. 모델 후보와 사전학습 모델 출처

Hugging Face에서 검토한 후보:

| 모델 | 용도 | 상태 |
|---|---|---|
| `klue/roberta-base` | 한국어 Transformer 후보 | 검토 |
| `klue/roberta-small` | 문맥 multi-label fine-tuning 파일럿 | noisy 1000 fast-track까지 재검토했으나 런타임 미채택 |
| `klue/roberta-small` 로컬 조건 라벨 모델 | 오타/무띄어쓰기/중간 길이 질의 조건 multi-label 후보 | `data/models/klue_roberta_small`로 materialize 후 2 epoch 학습, synthetic test는 높지만 런타임 미채택 |
| `bespin-global/klue-roberta-small-3i4k-intent-classification` | intent 관련 참고 후보 | 검토 |
| `j5ng/et5-typos-corrector` | 한국어 구어체 맞춤법/오타 교정 베이스 | 로컬 파일로 materialize 후 도메인 correction fine-tuning 완료, FastAPI 내부 로컬 모델로 제한 적용 |
| `quickspacer` | 한국어 띄어쓰기 전용 후보 | 500건 샘플에서 기준선보다 낮아 런타임 미채택 |

판단:

- 현재 기본 런타임은 규칙 기반 처리 + 문자 n-gram Naive Bayes 보조 + 정규화 레이어다.
- Transformer는 실험 후보이며, hard holdout/rotating blind/chat 평가에서 기준선 대비 이득과 latency를 확인하기 전까지 기본 경로로 교체하지 않는다.
- 2026-05-17 fast-track 실험은 `data/processed/context_finetune_20260517_human_light_1000/` split으로 수행했다. add-condition 경계 보정 후 `klue/roberta-small` 1 epoch rule hybrid hard test micro-F1은 0.9885로 당시 기준선 0.9908에 근접했지만 넘지 못했고, 3 epochs는 validation만 개선되어 런타임 채택하지 않았다.
- 이후 `soft_and`, optional facility, 제외/교체 경계를 더 점검하기 위해 `data/eval/tourism_context_rotating_blind_holdout_20260517_v5.jsonl`을 추가했다. v5는 보강에 사용된 진단셋이므로 최종 품질 점수로 재사용하지 않는다.

2026-05-18 조건 라벨 Transformer 로컬 학습:

| 항목 | 결과 |
|---|---:|
| 원본 조건 데이터 | 핵심어 변형 5,000 rows |
| deterministic 증강 | 10,000 rows |
| train / validation / test | 12,200 / 1,200 / 1,600 |
| 모델 | `data/models/klue_roberta_small` |
| 학습 | 2 epochs, batch 32, lr 2e-5, MPS |
| validation micro-F1 | 0.9904 |
| synthetic test micro-F1 | 0.9941 |
| synthetic test exact | 0.9925 |
| synthetic test latency | 1.32ms/row |
| rule baseline test micro-F1 | 0.8943 |
| corrected rule baseline test micro-F1 | 0.8920 |

해석:

- 조건 라벨 Transformer는 synthetic 조건 데이터에서 룰 기준선보다 높았다.
- 다만 학습/검증 데이터가 deterministic 증강을 포함하므로 바로 런타임 채택하지 않는다.
- 샘플 오류에서 `휠체어 대여 가격`, `부모님이랑 갈 만한 곳`, `휠체어 화장실` 같은 표현의 과해석이 확인됐다.
- 다음 단계는 fresh 중간 길이 chat 평가와 실제 카드 품질 평가에서 이득을 확인하는 것이다.

2026-05-18 quickspacer 띄어쓰기 후보 비교:

| 평가 | exact |
|---|---:|
| 수동/도메인 정규화 기준선 500건 | 0.838 |
| quickspacer 병행 500건 | 0.832 |

해석:

- quickspacer는 `입구에턱이없는`, `소리없이도안내를볼수있는` 같은 일부 무띄어쓰기 문장을 개선했다.
- 반대로 `바퀴의자 -> 바퀴의 자`, `이동약자 -> 이 동약자`, `음성안내 -> 음성 안 내`처럼 보호 표현을 손상했다.
- 따라서 현재 런타임에는 quickspacer를 적용하지 않는다.

### 한국어 전문 교정 모델 적용

오타/띄어쓰기 보강은 도메인 한정 정규화기만으로 끝내지 않고, 한국어 전문 교정 모델을 로컬 파일로 내려받은 뒤 프로젝트 데이터로 추가 학습했다. Hugging Face나 GitHub는 모델 탐색과 준비 단계의 출처일 뿐이며, 운영 경로에서는 원격 API 호출이나 런타임 다운로드를 사용하지 않는다. FastAPI는 `data/models/tourism_korean_corrector/`에 저장된 로컬 모델만 읽는다.

모델 파일이 없는 경우 원문/도메인 정규화 경로로 안전하게 degrade할 수는 있지만, 이것은 장애 대응 경로일 뿐 정상 배포 상태가 아니다. 정상 상태는 학습된 로컬 교정 모델이 서버에 포함되어 있고, 런타임 네트워크 없이 동작하는 것이다.

현재 기본 정책:

- `TOURISM_KOREAN_CORRECTION_ENABLED=true`
- `TOURISM_KOREAN_CORRECTION_RISKY_ONLY=true`
- `TOURISM_KOREAN_CORRECTION_ALLOW_DOWNLOAD=false`

따라서 기본값은 “로컬 교정 후보 레이어 ON”이지만, 무띄어쓰기/오타/정규화 위험 신호가 있는 문장에만 시도한다. Hugging Face 다운로드나 API 조회는 기본 경로에서 허용하지 않는다. 다운로드가 필요하면 개발자가 별도 준비 환경에서 명시적으로 켠 뒤 로컬 모델 디렉터리로 materialize한다.

교정 후보는 원문을 대체하지 않고 다음 후보 중 하나로만 평가한다.

```text
원문
-> 로컬 한국어 교정 후보
-> 도메인 정규화 후보
-> 로컬 교정 뒤 도메인 정규화 후보
-> 병렬 문맥 해석
```

파일럿 스크립트:

```bash
.venv/bin/python scripts/eval_korean_correction_candidates.py --limit 120 --use-default-hf-model --device auto
```

로컬 학습 파이프라인:

```bash
.venv/bin/python scripts/prepare_tourism_korean_correction_finetune_data.py
.venv/bin/python scripts/materialize_korean_correction_base_model.py --local-files-only
.venv/bin/python scripts/train_tourism_korean_corrector.py \
  --epochs 5 \
  --batch-size 8 \
  --eval-steps 100 \
  --save-steps 100 \
  --early-stopping-patience 4 \
  --device cpu \
  --output-dir data/models/tourism_korean_corrector
```

산출물:

| 파일 | 용도 |
|---|---|
| `data/generated/tour_api/korean_correction_candidates/audit.json` | 원문/도메인 정규화/교정 후보/교정+도메인 비교 지표 |
| `data/generated/tour_api/korean_correction_candidates/samples.jsonl` | 실제 교정 문장, 라벨 변화, 보호 단어 훼손 샘플 |
| `data/processed/korean_correction_finetune/train.jsonl` | 로컬 교정 모델 fine-tuning train split |
| `data/processed/korean_correction_finetune/validation.jsonl` | 로컬 교정 모델 validation split |
| `data/models/tourism_korean_corrector/training_manifest.json` | 로컬 교정 모델 학습 조건과 best checkpoint 기록 |

2026-05-17 파일럿 결과:

| 평가셋 | 입력 후보 | exact | micro-F1 | mismatch rows |
|---|---|---:|---:|---:|
| noisy human-light 120 | 원문 | 0.3750 | 0.6857 | 75 |
| noisy human-light 120 | 도메인 정규화 | 0.3750 | 0.6857 | 75 |
| noisy human-light 120 | `j5ng/et5-typos-corrector` | 0.4000 | 0.7169 | 72 |
| noisy human-light 120 | 교정 후보 뒤 도메인 정규화 | 0.4000 | 0.7169 | 72 |
| noisy human-light 1000 | 원문 | 0.3260 | 0.6700 | 674 |
| noisy human-light 1000 | 도메인 정규화 | 0.3170 | 0.6610 | 683 |
| noisy human-light 1000 | `j5ng/et5-typos-corrector` | 0.3370 | 0.6947 | 663 |
| noisy human-light 1000 | 보호 단어 guard 적용 교정 후보 | 0.3370 | 0.6947 | 663 |
| rotating blind v5 | 원문 | 0.8475 | 0.9457 | 9 |
| rotating blind v5 | 도메인 정규화 | 0.8475 | 0.9457 | 9 |
| rotating blind v5 | `j5ng/et5-typos-corrector` | 0.8136 | 0.9341 | 11 |
| rotating blind v5 | 보호 단어 guard 적용 교정 후보 | 0.8136 | 0.9341 | 11 |
| chat blind v2 | 원문 | 15/15 통과 | - | 0 |
| chat blind v2 | 교정 후보 | 최초 14/15, 보강 후 15/15 통과 | - | 0 |

해석:

- noisy 1000에서는 교정 후보가 원문보다 micro-F1을 올렸다.
- noisy 1000에서 `유모차이동`을 `유아 차이동`으로 바꾼 보호 단어 훼손 1건이 있었다. 따라서 교정 결과에 보호 단어가 사라지면 해당 후보는 버린다.
- rotating blind v5에서는 교정 후보가 원문보다 낮았다. 예를 들어 `오래 줄 서지 않아도`가 `오래 줄 서서 보지 않아도`로 바뀌며 mobility signal이 약해졌고, `점자블록`이 `점자 블록`으로 바뀌며 현행 facility rule을 통과하지 못했다.
- 실제 chat blind v2에서는 교정 후보가 처음에는 1건 실패했다. `남제주군`이 `남 제주군`으로 바뀌면서 과거 지명 매핑이 깨진 것이 원인이었다. 이후 정규화기에 `남 제주군 -> 남제주군` 같은 과거 지명 띄어쓰기 복원을 추가했고 corrected chat 평가도 15/15로 회복했다.
- 결론은 제한적 런타임 적용이다. 교정 후보 레이어는 기본 ON이지만 전체 입력에 항상 적용하지 않고, 무띄어쓰기/오타 위험 태그가 있는 문장에 한정해 후보로만 비교한다.
- 다음 판단은 실제 `/tourism/chat` 카드 평가에서 교정 후보가 카드 품질을 올리는지로 한다.

2026-05-18 로컬 fine-tuning 결과:

| 항목 | 결과 |
|---|---|
| 학습 데이터 | train 5,453 rows, validation 605 rows |
| 베이스 모델 | `data/models/tourism_korean_corrector_base` |
| 최종 모델 | `data/models/tourism_korean_corrector` |
| CPU/MPS 짧은 벤치 | CPU 29.83초, MPS 47.58초로 CPU 채택 |
| 학습 방식 | mini-batch 8, 최대 5 epochs, 100 step마다 validation, early stopping patience 4 |
| 종료 지점 | 2,900 step, epoch 4.252에서 early stopping |
| best validation loss | 0.0631057620 at checkpoint 2500 |
| validation exact accuracy | 0.7107 |
| validation compact accuracy | 0.7488 |
| validation mean similarity | 0.9494 |
| 런타임 정책 | FastAPI가 로컬 모델 디렉터리만 로드, 런타임 네트워크 호출 금지 |

추가 fine-tuning/decoding 점검:

| 후보 | validation loss | exact accuracy | compact accuracy | 판단 |
|---|---:|---:|---:|---|
| 기존 모델, beams=3 | 0.0631057620 | 0.7107 | 0.7488 | 기준 |
| 2단계 fine-tuning lr=1e-5, wd=0.01 | 0.0627810955 | 0.7091 | 0.7438 | loss는 개선됐지만 accuracy 하락, 미채택 |
| 2단계 fine-tuning lr=5e-6 | 0.0616126321 | 0.7025 | 0.7339 | loss는 개선됐지만 accuracy 하락, 미채택 |
| 기존 모델, beams=1 | 0.0631057620 | 0.7124 | 0.7521 | accuracy와 속도 모두 유리, 런타임 채택 |
| 기존 모델, beams=4 | 0.0631057620 | 0.7124 | 0.7521 | accuracy는 동일하지만 beams=1보다 느림, 미채택 |

해석:

- validation loss만으로 교정 모델을 고르면 실제 문장 정확도가 떨어질 수 있다.
- 현재는 추가 fine-tuning 모델을 승격하지 않고, 기존 best 모델에 `num_beams=1` decoding을 적용한다.
- 다음 fine-tuning을 다시 시도할 때는 loss뿐 아니라 exact/compact accuracy를 모델 선택 기준에 반드시 포함한다.

적용 확인:

| 입력 | 로컬 교정 후보 | 서비스 해석 |
|---|---|---|
| `서울 강남구 근처에서 휄체어 관광지 추천해줘` | `서울 강남구 근처에서 휠체어 관광지 추천해줘` | 지역 `서울 강남구`, 조건 `휠체어` |
| `서울강남구휄체어관광지추천` | `서울강남구 휠체어 관광지 추천` | 지역 `강남구`, 조건 `휠체어` |
| `부산엘베있는실내관광지` | `부산 엘리베이터 있는 실내 관광지` | 지역 `부산`, 조건 `엘리베이터` |

주의:

- 로컬 교정 모델은 원문을 무조건 대체하지 않는다. 원문, 도메인 정규화, 교정 후보를 함께 비교하고 보호 단어 훼손이 있으면 교정 후보를 버린다.
- 지명이 손상되면 나머지 조건까지 버리지 않고, 지역 확인/추가 질의로 이어지게 한다.
- “한국어 전체를 이해하는 범용 교정기”가 아니라, 무장애 관광 추천 입력을 기존 파서가 읽기 쉬운 형태로 보정하는 런타임 후보 모델이다.

### noisy chat 평가 추가

2026-05-17에는 실제 사용자가 띄어쓰기와 오타를 많이 낸다는 전제로 noisy chat 평가셋을 추가했다.

파일:

| 파일 | rows | 용도 |
|---|---:|---|
| `data/eval/tourism_noisy_chat_eval_20260517.jsonl` | 15 | 오타, 무띄어쓰기, 과거 지명, 복수 지역 모호성, 맥락 없는 후속 표현 검증 |
| `data/generated/tour_api/eval_runs/tourism_noisy_chat_eval_20260517_baseline.jsonl` | 15 | 보강 전 결과 |
| `data/generated/tour_api/eval_runs/tourism_noisy_chat_eval_20260517_after_normalizer_patch.jsonl` | 15 | 보강 후 결과 |

결과:

| 평가 | 통과 | 실패 | 주요 실패/보강 |
|---|---:|---:|---|
| baseline | 10 | 5 | `남제주군` 내부 분리, `부산중구`/`서울중구` 미분리, `서울부산` 임의 지역 확정 |
| 정규화 보강 후 | 15 | 0 | 과거 지명 재결합, compact 광역+중구 복원, 복수 광역 지역 clarification 처리 |

해석:

- 오타/무띄어쓰기 처리는 계속 도메인 한정 정규화기로 보강한다.
- `서울부산휠체어추천`처럼 복수 지역이 붙은 문장은 서울 또는 부산으로 임의 확정하지 않고 추가 질의한다.
- `점자블록있는곳`, `시장말고조용한데`처럼 지역이 없는 조건/후속형 문장은 카드 추천보다 지역 확인을 먼저 요청한다.

### GPT-style 핵심어 변형 학습 데이터

목적:

- 사람이 `휄체어`, `휠쳐` 같은 오타를 하나씩 추가하는 방식에서 벗어난다.
- GPT/LLM 생성 후보로 무장애 핵심어의 오타, 띄어쓰기 붕괴, 축약어, 동의어, 우회 표현, 반례를 넓게 모은다.
- 바로 런타임에 넣지 않고, 현재 파서가 못 잡는 표현을 review queue와 승격 후보로 분리한다.

가공:

- GPT 프롬프트 생성: `scripts/build_tourism_keyword_variant_generation_prompt.py`
- GPT-style seed 생성: `scripts/generate_tourism_keyword_variant_seed.py`
- schema/라벨/중복/현재 파서 커버율 검증: `scripts/validate_tourism_keyword_variant_dataset.py`
- 승격 후보 요약: `scripts/build_tourism_keyword_promotion_candidates.py`

산출물:

| 파일 | rows | 용도 |
|---|---:|---|
| `data/generated/tour_api/keyword_variant_prompts/keyword_variant_generation_prompt_20260518_001.md` | - | GPT에 줄 핵심어 변형 데이터 생성 프롬프트 |
| `data/generated/tour_api/keyword_variant_batches/keyword_variant_batch_20260518_gpt_style_2400.raw.jsonl` | 2,400 | GPT-style 핵심어 변형 원본 |
| `data/processed/tourism_keyword_variants_20260518.valid.jsonl` | 2,400 | 검증 통과 데이터 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_report.json` | - | 현재 파서 커버율 리포트 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_review_queue.jsonl` | 756 | 승격 후보 중 현재 파서가 못 잡는 row |
| `data/processed/tourism_keyword_promotion_candidates_20260518.json` | - | 조건별 사전/동의어 승격 후보 요약 |
| `data/generated/tour_api/keyword_variant_prompts/keyword_variant_generation_prompt_20260518_5000.md` | - | GPT에 줄 5,000건 핵심어 변형 생성 프롬프트 |
| `data/generated/tour_api/keyword_variant_batches/keyword_variant_batch_20260518_gpt_style_5000.raw.jsonl` | 5,000 | GPT-style 핵심어 변형 5,000건 원본 |
| `data/processed/tourism_keyword_variants_20260518_5000.valid.jsonl` | 5,000 | 검증 통과 5,000건 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_report.json` | - | 5,000건 현재 파서 커버율 리포트 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_review_queue.jsonl` | 1,645 | 5,000건 기준 승격 후보 중 현재 파서 미커버 row |
| `data/processed/tourism_keyword_promotion_candidates_20260518_5000.json` | - | 5,000건 기준 조건별 승격 후보 요약 |
| `data/processed/tourism_keyword_variants_20260518_5000.after_promotion.valid.jsonl` | 5,000 | 안전 후보 반영 후 재검증 결과 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_after_promotion_report.json` | - | 안전 후보 반영 후 현재 파서 커버율 리포트 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_after_promotion_review_queue.jsonl` | 726 | 안전 후보 반영 후에도 남은 승격 후보 미커버 row |
| `data/processed/tourism_keyword_variants_20260518_5000.after_bucket_patch.valid.jsonl` | 5,000 | bucket 분석 후 과해석 제거/문장형 후보 일부 반영 재검증 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_after_bucket_patch_report.json` | - | bucket 보강 후 현재 파서 커버율 리포트 |
| `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_after_bucket_patch_review_queue.jsonl` | 159 | bucket 보강 후 남은 승격 후보 미커버 row |
| `data/generated/tour_api/keyword_variant_reports/keyword_correction_coverage_20260518.json` | - | 수동/도메인 정규화 파서와 로컬 교정 모델 병행 경로 비교 |
| `data/generated/tour_api/keyword_variant_reports/keyword_correction_coverage_20260518_samples.jsonl` | - | 교정 모델 병행으로 개선/회귀된 샘플 |

분포:

| 구분 | rows |
|---|---:|
| typo | 385 |
| spacing | 428 |
| abbreviation | 438 |
| synonym | 432 |
| paraphrase | 438 |
| negative | 158 |
| ambiguous | 121 |

5,000건 확장 분포:

| 구분 | rows |
|---|---:|
| typo | 871 |
| spacing | 914 |
| abbreviation | 906 |
| synonym | 943 |
| paraphrase | 961 |
| negative | 223 |
| ambiguous | 182 |

검증 결과:

| 항목 | rows |
|---|---:|
| valid rows | 2,400 |
| rejected rows | 0 |
| 현재 파서 exact | 1,218 |
| 현재 파서 mismatch | 1,182 |
| promote candidate | 1,846 |
| promote candidate mismatch | 756 |

5,000건 검증 결과:

| 항목 | rows |
|---|---:|
| valid rows | 5,000 |
| rejected rows | 0 |
| 현재 파서 exact | 2,607 |
| 현재 파서 mismatch | 2,393 |
| promote candidate | 3,994 |
| promote candidate mismatch | 1,645 |

5,000건 리포트 기반 보강 결과:

| 항목 | 최초 | 1차 안전 후보 반영 | bucket 보강 후 |
|---|---:|---:|---:|
| 현재 파서 exact | 2,607 | 3,563 | 4,298 |
| 현재 파서 mismatch | 2,393 | 1,437 | 702 |
| promote candidate mismatch | 1,645 | 726 | 159 |

5,000건 기준 수동 정규화와 로컬 교정 모델 병행 비교:

| 항목 | 수동/도메인 정규화 | 로컬 교정 모델 병행 |
|---|---:|---:|
| 전체 exact accuracy | 0.8596 | 0.8598 |
| 전체 exact rows | 4,298 / 5,000 | 4,299 / 5,000 |
| promote 후보 exact accuracy | 0.9602 | 0.9604 |
| non-promote exact accuracy | 0.4602 | 0.4602 |
| missing condition rows | 177 | 176 |
| extra condition rows | 532 | 537 |
| 개선 row | - | 1 |
| 회귀 row | - | 0 |

해석:

- 현재 5,000건은 이미 수동/도메인 정규화 보강이 많이 들어간 후라 로컬 교정 모델의 추가 이득은 1건에 그쳤다.
- 개선된 1건은 `리프트기준으로부산중구산책코스되는곳`을 엘리베이터/승강 설비 맥락으로 보정한 사례다.
- 회귀가 0건인 점은 긍정적이지만, extra condition rows가 532건에서 537건으로 늘었으므로 로컬 교정 모델을 원문 대체기로 쓰면 안 된다.
- 결론은 현행 유지다. 런타임에서는 로컬 교정 모델을 기본 ON 후보 레이어로 두되, 원문/도메인 정규화 후보와 함께 비교하고 보호 단어 훼손이나 과해석이 있으면 버린다.

보강 방식:

- 바로 모든 후보를 사전에 넣지 않았다.
- `휠쳐`, `휠 체어`, `보조갼`, `앨리베이터`, `출입 통로`, `무단차`, `자 막`, `청각 장애`, `무릎 불편`처럼 의미 충돌 가능성이 낮은 오타/띄어쓰기 후보를 정규화기에 반영했다.
- `바퀴 의자`, `무단차`, `평탄한 길`, `입구에 턱이 없는`, `부모님이 무리 없는`, `영상안내`처럼 도메인 의미가 명확한 후보를 조건 키워드에 추가했다.
- 726건을 다시 분석해 `missing_only`, `extra_only`, `both`로 나눴다. `장애인 주차/화장실/보조견`에서 `장애인` 하나 때문에 `휠체어`가 추가되는 과해석은 제거했다.
- `층 이동이 편한`, `위아래 이동이 쉬운`, `계단 말고 올라갈`, `손으로 만져 확인할 안내`, `소리 없이도 안내를 볼 수`, `유모차 바퀴가 걸리지`처럼 의미가 비교적 분명한 문장형 후보만 일부 반영했다.
- `리프트` 단독은 차량/예약 의미와 충돌할 수 있어 보류했다. 다만 `휠체어 리프트`, `장애인 리프트`, `승강 리프트`, `승강용 리프트`, `계단 리프트`, `지하철 리프트`, `시설 리프트`, `건물 리프트`, `관광시설 리프트`, `공공기관 리프트`처럼 접근성 설비 맥락이 분명한 표현은 엘리베이터/승강 설비 조건으로 반영했다. 공공기관으로만 한정하지 않는다.

현재 파서가 많이 놓친 조건:

| 조건 | missing |
|---|---:|
| 접근로 | 157 |
| 고령자 | 146 |
| 엘리베이터 | 103 |
| 휠체어 | 74 |
| 청각장애 | 59 |
| 보조견 | 39 |
| 시각장애 | 31 |
| 유모차 | 26 |
| 주차 | 20 |

5,000건에서 현재 파서가 많이 놓친 조건:

| 조건 | missing |
|---|---:|
| 접근로 | 336 |
| 고령자 | 314 |
| 엘리베이터 | 242 |
| 휠체어 | 166 |
| 청각장애 | 136 |
| 시각장애 | 97 |
| 보조견 | 81 |
| 유모차 | 63 |
| 주차 | 40 |

해석:

- `바퀴 의자`, `휠쳐`, `휠 체어`, `무단차`, `평탄한 길`, `입구에 턱이 없는`, `부모님이 무리 없는`, `영상안내`, `자 막` 같은 표현이 승격 후보로 분리됐다.
- paraphrase는 과보정 위험이 있으므로 바로 키워드 사전에 넣기보다 문맥 분류기/Transformer 학습 후보로 우선 사용한다.
- negative/ambiguous row는 핵심어가 보인다는 이유만으로 조건을 확정하지 않도록 하는 반례 데이터다.

## 7. 사용하지 않거나 제한한 데이터

| 데이터 | 판단 |
|---|---|
| Hugging Face external utterances 전체 | 기본 학습 제외. taxonomy 재라벨링 전까지 실험 후보 |
| Gemini verified holdout | 학습 제외. 평가/문제 탐색 전용 |
| 기존 blind/rotating holdout | 한 번 보강에 사용한 뒤 최종 품질 점수로 재사용하지 않음 |
| 일반 관광 검색 결과 중 무장애 상세 없는 후보 | 접근성 카드로 편입하지 않음 |
| AI Hub 원본 전체 | 직접 학습하지 않음. 고신뢰 일부만 추출 |

## 8. 설명할 때 주의할 표현

사용해도 되는 표현:

- “한국관광공사 TourAPI와 무장애 여행 정보에서 확인된 관광 카드 근거를 사용했다.”
- “AI Hub 대화 데이터는 의도 분류 보강에 사용했고, 문맥 라벨에는 직접 사용하지 않았다.”
- “Hugging Face 공개 발화는 실험 후보로 검토했지만 기본 런타임 학습에는 넣지 않았다.”
- “Gemini/Codex 생성 데이터는 사람 작성 데이터가 아니라 AI-generated holdout 또는 human-light 보강 데이터로 구분했다.”

피해야 할 표현:

- “AI Hub로 문맥 이해 모델을 학습했다.”  
  실제로는 의도 분류 일부에만 사용했다.
- “Hugging Face 데이터를 학습에 사용했다.”  
  기본 학습에는 제외했다.
- “Gemini holdout으로 성능을 증명했다.”  
  평가/문제 탐색용이지 최종 품질 증명이 아니다.
- “무장애 상세이 없는 일반 관광지도 접근성 추천 카드로 썼다.”  
  공식 무장애 상세 근거가 없으면 접근성 카드로 편입하지 않는다.
